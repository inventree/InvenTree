"""Provides helper functions used throughout the InvenTree project."""

import hashlib
import io
import json
import logging
import os
import os.path
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.exceptions import FieldError, ValidationError
from django.core.files.storage import default_storage
from django.core.validators import URLValidator
from django.http import StreamingHttpResponse
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

import regex
import requests
from bleach import clean
from djmoney.money import Money
from PIL import Image

import InvenTree.version
from common.models import InvenTreeSetting
from common.notifications import (InvenTreeNotificationBodies,
                                  NotificationBody, trigger_notification)
from common.settings import currency_code_default

from .api_tester import UserMixin
from .settings import MEDIA_URL, STATIC_URL

logger = logging.getLogger('inventree')


def getSetting(key, backup_value=None):
    """Shortcut for reading a setting value from the database."""
    return InvenTreeSetting.get_setting(key, backup_value=backup_value)


def generateTestKey(test_name):
    """Generate a test 'key' for a given test name. This must not have illegal chars as it will be used for dict lookup in a template.

    Tests must be named such that they will have unique keys.
    """
    key = test_name.strip().lower()
    key = key.replace(" ", "")

    # Remove any characters that cannot be used to represent a variable
    key = re.sub(r'[^a-zA-Z0-9]', '', key)

    return key


def constructPathString(path, max_chars=250):
    """Construct a 'path string' for the given path.

    Arguments:
        path: A list of strings e.g. ['path', 'to', 'location']
        max_chars: Maximum number of characters
    """

    pathstring = '/'.join(path)

    # Replace middle elements to limit the pathstring
    if len(pathstring) > max_chars:
        n = int(max_chars / 2 - 2)
        pathstring = pathstring[:n] + "..." + pathstring[-n:]

    return pathstring


def getMediaUrl(filename):
    """Return the qualified access path for the given file, under the media directory."""
    return os.path.join(MEDIA_URL, str(filename))


def getStaticUrl(filename):
    """Return the qualified access path for the given file, under the static media directory."""
    return os.path.join(STATIC_URL, str(filename))


def construct_absolute_url(*arg):
    """Construct (or attempt to construct) an absolute URL from a relative URL.

    This is useful when (for example) sending an email to a user with a link
    to something in the InvenTree web framework.

    This requires the BASE_URL configuration option to be set!
    """
    base = str(InvenTreeSetting.get_setting('INVENTREE_BASE_URL'))

    url = '/'.join(arg)

    if not base:
        return url

    # Strip trailing slash from base url
    if base.endswith('/'):
        base = base[:-1]

    if url.startswith('/'):
        url = url[1:]

    url = f"{base}/{url}"

    return url


def download_image_from_url(remote_url, timeout=2.5):
    """Download an image file from a remote URL.

    This is a potentially dangerous operation, so we must perform some checks:

    - The remote URL is available
    - The Content-Length is provided, and is not too large
    - The file is a valid image file

    Arguments:
        remote_url: The remote URL to retrieve image
        max_size: Maximum allowed image size (default = 1MB)
        timeout: Connection timeout in seconds (default = 5)

    Returns:
        An in-memory PIL image file, if the download was successful

    Raises:
        requests.exceptions.ConnectionError: Connection could not be established
        requests.exceptions.Timeout: Connection timed out
        requests.exceptions.HTTPError: Server responded with invalid response code
        ValueError: Server responded with invalid 'Content-Length' value
        TypeError: Response is not a valid image
    """

    # Check that the provided URL at least looks valid
    validator = URLValidator()
    validator(remote_url)

    # Calculate maximum allowable image size (in bytes)
    max_size = int(InvenTreeSetting.get_setting('INVENTREE_DOWNLOAD_IMAGE_MAX_SIZE')) * 1024 * 1024

    try:
        response = requests.get(
            remote_url,
            timeout=timeout,
            allow_redirects=True,
            stream=True,
        )
        # Throw an error if anything goes wrong
        response.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        raise Exception(_("Connection error") + f": {str(exc)}")
    except requests.exceptions.Timeout as exc:
        raise exc
    except requests.exceptions.HTTPError:
        raise requests.exceptions.HTTPError(_("Server responded with invalid status code") + f": {response.status_code}")
    except Exception as exc:
        raise Exception(_("Exception occurred") + f": {str(exc)}")

    if response.status_code != 200:
        raise Exception(_("Server responded with invalid status code") + f": {response.status_code}")

    try:
        content_length = int(response.headers.get('Content-Length', 0))
    except ValueError:
        raise ValueError(_("Server responded with invalid Content-Length value"))

    if content_length > max_size:
        raise ValueError(_("Image size is too large"))

    # Download the file, ensuring we do not exceed the reported size
    fo = io.BytesIO()

    dl_size = 0
    chunk_size = 64 * 1024

    for chunk in response.iter_content(chunk_size=chunk_size):
        dl_size += len(chunk)

        if dl_size > max_size:
            raise ValueError(_("Image download exceeded maximum size"))

        fo.write(chunk)

    if dl_size == 0:
        raise ValueError(_("Remote server returned empty response"))

    # Now, attempt to convert the downloaded data to a valid image file
    # img.verify() will throw an exception if the image is not valid
    try:
        img = Image.open(fo).convert()
        img.verify()
    except Exception:
        raise TypeError(_("Supplied URL is not a valid image file"))

    return img


def TestIfImage(img):
    """Test if an image file is indeed an image."""
    try:
        Image.open(img).verify()
        return True
    except Exception:
        return False


def getBlankImage():
    """Return the qualified path for the 'blank image' placeholder."""
    return getStaticUrl("img/blank_image.png")


def getBlankThumbnail():
    """Return the qualified path for the 'blank image' thumbnail placeholder."""
    return getStaticUrl("img/blank_image.thumbnail.png")


def getLogoImage(as_file=False, custom=True):
    """Return the InvenTree logo image, or a custom logo if available."""

    """Return the path to the logo-file."""
    if custom and settings.CUSTOM_LOGO:

        static_storage = StaticFilesStorage()

        if static_storage.exists(settings.CUSTOM_LOGO):
            storage = static_storage
        elif default_storage.exists(settings.CUSTOM_LOGO):
            storage = default_storage
        else:
            storage = None

        if storage is not None:
            if as_file:
                return f"file://{storage.path(settings.CUSTOM_LOGO)}"
            else:
                return storage.url(settings.CUSTOM_LOGO)

    # If we have got to this point, return the default logo
    if as_file:
        path = settings.STATIC_ROOT.joinpath('img/inventree.png')
        return f"file://{path}"
    else:
        return getStaticUrl('img/inventree.png')


def getSplashScren(custom=True):
    """Return the InvenTree splash screen, or a custom splash if available"""

    static_storage = StaticFilesStorage()

    if custom and settings.CUSTOM_SPLASH:

        if static_storage.exists(settings.CUSTOM_SPLASH):
            return static_storage.url(settings.CUSTOM_SPLASH)

    # No custom splash screen
    return static_storage.url("img/inventree_splash.jpg")


def TestIfImageURL(url):
    """Test if an image URL (or filename) looks like a valid image format.

    Simply tests the extension against a set of allowed values
    """
    return os.path.splitext(os.path.basename(url))[-1].lower() in [
        '.jpg', '.jpeg', '.j2k',
        '.png', '.bmp',
        '.tif', '.tiff',
        '.webp', '.gif',
    ]


def str2bool(text, test=True):
    """Test if a string 'looks' like a boolean value.

    Args:
        text: Input text
        test (default = True): Set which boolean value to look for

    Returns:
        True if the text looks like the selected boolean value
    """
    if test:
        return str(text).lower() in ['1', 'y', 'yes', 't', 'true', 'ok', 'on', ]
    else:
        return str(text).lower() in ['0', 'n', 'no', 'none', 'f', 'false', 'off', ]


def str2int(text, default=None):
    """Convert a string to int if possible

    Args:
        text: Int like string
        default: Return value if str is no int like

    Returns:
        Converted int value
    """
    try:
        return int(text)
    except Exception:
        return default


def is_bool(text):
    """Determine if a string value 'looks' like a boolean."""
    if str2bool(text, True):
        return True
    elif str2bool(text, False):
        return True
    else:
        return False


def isNull(text):
    """Test if a string 'looks' like a null value. This is useful for querying the API against a null key.

    Args:
        text: Input text

    Returns:
        True if the text looks like a null value
    """
    return str(text).strip().lower() in ['top', 'null', 'none', 'empty', 'false', '-1', '']


def normalize(d):
    """Normalize a decimal number, and remove exponential formatting."""
    if type(d) is not Decimal:
        d = Decimal(d)

    d = d.normalize()

    # Ref: https://docs.python.org/3/library/decimal.html
    return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()


def increment(value):
    """Attempt to increment an integer (or a string that looks like an integer).

    e.g.

    001 -> 002
    2 -> 3
    AB01 -> AB02
    QQQ -> QQQ

    """
    value = str(value).strip()

    # Ignore empty strings
    if value in ['', None]:
        # Provide a default value if provided with a null input
        return '1'

    pattern = r"(.*?)(\d+)?$"

    result = re.search(pattern, value)

    # No match!
    if result is None:
        return value

    groups = result.groups()

    # If we cannot match the regex, then simply return the provided value
    if len(groups) != 2:
        return value

    prefix, number = groups

    # No number extracted? Simply return the prefix (without incrementing!)
    if not number:
        return prefix

    # Record the width of the number
    width = len(number)

    try:
        number = int(number) + 1
        number = str(number)
    except ValueError:
        pass

    number = number.zfill(width)

    return prefix + number


def decimal2string(d):
    """Format a Decimal number as a string, stripping out any trailing zeroes or decimal points. Essentially make it look like a whole number if it is one.

    Args:
        d: A python Decimal object

    Returns:
        A string representation of the input number
    """
    if type(d) is Decimal:
        d = normalize(d)

    try:
        # Ensure that the provided string can actually be converted to a float
        float(d)
    except ValueError:
        # Not a number
        return str(d)

    s = str(d)

    # Return entire number if there is no decimal place
    if '.' not in s:
        return s

    return s.rstrip("0").rstrip(".")


def decimal2money(d, currency=None):
    """Format a Decimal number as Money.

    Args:
        d: A python Decimal object
        currency: Currency of the input amount, defaults to default currency in settings

    Returns:
        A Money object from the input(s)
    """
    if not currency:
        currency = currency_code_default()
    return Money(d, currency)


def WrapWithQuotes(text, quote='"'):
    """Wrap the supplied text with quotes.

    Args:
        text: Input text to wrap
        quote: Quote character to use for wrapping (default = "")

    Returns:
        Supplied text wrapped in quote char
    """
    if not text.startswith(quote):
        text = quote + text

    if not text.endswith(quote):
        text = text + quote

    return text


def MakeBarcode(cls_name, object_pk: int, object_data=None, **kwargs):
    """Generate a string for a barcode. Adds some global InvenTree parameters.

    Args:
        object_type: string describing the object type e.g. 'StockItem'
        object_id: ID (Primary Key) of the object in the database
        object_url: url for JSON API detail view of the object
        data: Python dict object containing extra datawhich will be rendered to string (must only contain stringable values)

    Returns:
        json string of the supplied data plus some other data
    """

    if object_data is None:
        object_data = {}

    brief = kwargs.get('brief', True)

    data = {}

    if brief:
        data[cls_name] = object_pk
    else:
        data['tool'] = 'InvenTree'
        data['version'] = InvenTree.version.inventreeVersion()
        data['instance'] = InvenTree.version.inventreeInstanceName()

        # Ensure PK is included
        object_data['id'] = object_pk
        data[cls_name] = object_data

    return json.dumps(data, sort_keys=True)


def GetExportFormats():
    """Return a list of allowable file formats for exporting data."""
    return [
        'csv',
        'tsv',
        'xls',
        'xlsx',
        'json',
        'yaml',
    ]


def DownloadFile(data, filename, content_type='application/text', inline=False) -> StreamingHttpResponse:
    """Create a dynamic file for the user to download.

    Args:
        data: Raw file data (string or bytes)
        filename: Filename for the file download
        content_type: Content type for the download
        inline: Download "inline" or as attachment? (Default = attachment)

    Return:
        A StreamingHttpResponse object wrapping the supplied data
    """
    filename = WrapWithQuotes(filename)

    if type(data) == str:
        wrapper = FileWrapper(io.StringIO(data))
    else:
        wrapper = FileWrapper(io.BytesIO(data))

    response = StreamingHttpResponse(wrapper, content_type=content_type)
    response['Content-Length'] = len(data)

    disposition = "inline" if inline else "attachment"

    response['Content-Disposition'] = f'{disposition}; filename={filename}'

    return response


def increment_serial_number(serial: str):
    """Given a serial number, (attempt to) generate the *next* serial number.

    Note: This method is exposed to custom plugins.

    Arguments:
        serial: The serial number which should be incremented

    Returns:
        incremented value, or None if incrementing could not be performed.
    """

    from plugin.registry import registry

    # Ensure we start with a string value
    if serial is not None:
        serial = str(serial).strip()

    # First, let any plugins attempt to increment the serial number
    for plugin in registry.with_mixin('validation'):
        result = plugin.increment_serial_number(serial)
        if result is not None:
            return str(result)

    # If we get to here, no plugins were able to "increment" the provided serial value
    # Attempt to perform increment according to some basic rules
    return increment(serial)


def extract_serial_numbers(input_string, expected_quantity: int, starting_value=None):
    """Extract a list of serial numbers from a provided input string.

    The input string can be specified using the following concepts:

    - Individual serials are separated by comma: 1, 2, 3, 6,22
    - Sequential ranges with provided limits are separated by hyphens: 1-5, 20 - 40
    - The "next" available serial number can be specified with the tilde (~) character
    - Serial numbers can be supplied as <start>+ for getting all expecteded numbers starting from <start>
    - Serial numbers can be supplied as <start>+<length> for getting <length> numbers starting from <start>

    Actual generation of sequential serials is passed to the 'validation' plugin mixin,
    allowing custom plugins to determine how serial values are incremented.

    Arguments:
        input_string: Input string with specified serial numbers (string, or integer)
        expected_quantity: The number of (unique) serial numbers we expect
        starting_value: Provide a starting value for the sequence (or None)
    """

    if starting_value is None:
        starting_value = increment_serial_number(None)

    try:
        expected_quantity = int(expected_quantity)
    except ValueError:
        raise ValidationError([_("Invalid quantity provided")])

    if input_string:
        input_string = str(input_string).strip()
    else:
        input_string = ''

    if len(input_string) == 0:
        raise ValidationError([_("Empty serial number string")])

    next_value = increment_serial_number(starting_value)

    # Substitute ~ character with latest value
    while '~' in input_string and next_value:
        input_string = input_string.replace('~', str(next_value), 1)
        next_value = increment_serial_number(next_value)

    # Split input string by whitespace or comma (,) characters
    groups = re.split(r"[\s,]+", input_string)

    serials = []
    errors = []

    def add_error(error: str):
        """Helper function for adding an error message"""
        if error not in errors:
            errors.append(error)

    def add_serial(serial):
        """Helper function to check for duplicated values"""

        serial = serial.strip()

        # Ignore blank / emtpy serials
        if len(serial) == 0:
            return

        if serial in serials:
            add_error(_("Duplicate serial") + f": {serial}")
        else:
            serials.append(serial)

    # If the user has supplied the correct number of serials, do not split into groups
    if len(groups) == expected_quantity:
        for group in groups:
            add_serial(group)

        if len(errors) > 0:
            raise ValidationError(errors)
        else:
            return serials

    for group in groups:

        # Calculate the "remaining" quantity of serial numbers
        remaining = expected_quantity - len(serials)

        group = group.strip()

        if '-' in group:
            """Hyphen indicates a range of values:
            e.g. 10-20
            """
            items = group.split('-')

            if len(items) == 2:
                a = items[0]
                b = items[1]

                if a == b:
                    # Invalid group
                    add_error(_("Invalid group range: {g}").format(g=group))
                    continue

                group_items = []

                count = 0

                a_next = a

                while a_next is not None and a_next not in group_items:
                    group_items.append(a_next)
                    count += 1

                    # Progress to the 'next' sequential value
                    a_next = str(increment_serial_number(a_next))

                    if a_next == b:
                        # Successfully got to the end of the range
                        group_items.append(b)
                        break

                    elif count > remaining:
                        # More than the allowed number of items
                        break

                    elif a_next is None:
                        break

                if len(group_items) > remaining:
                    add_error(_("Group range {g} exceeds allowed quantity ({q})".format(g=group, q=expected_quantity)))
                elif len(group_items) > 0 and group_items[0] == a and group_items[-1] == b:
                    # In this case, the range extraction looks like it has worked
                    for item in group_items:
                        add_serial(item)
                else:
                    add_error(_("Invalid group range: {g}").format(g=group))

            else:
                # In the case of a different number of hyphens, simply add the entire group
                add_serial(group)

        elif '+' in group:
            """Plus character (+) indicates either:
            - <start>+ - Expected number of serials, beginning at the specified 'start' character
            - <start>+<num> - Specified number of serials, beginning at the specified 'start' character
            """
            items = group.split('+')

            sequence_items = []
            counter = 0
            sequence_count = max(0, expected_quantity - len(serials))

            if len(items) > 2 or len(items) == 0:
                add_error(_("Invalid group sequence: {g}").format(g=group))
                continue
            elif len(items) == 2:
                try:
                    if items[1]:
                        sequence_count = int(items[1]) + 1
                except ValueError:
                    add_error(_("Invalid group sequence: {g}").format(g=group))
                    continue

            value = items[0]

            # Keep incrementing up to the specified quantity
            while value is not None and value not in sequence_items and counter < sequence_count:
                sequence_items.append(value)
                value = increment_serial_number(value)
                counter += 1

            if len(sequence_items) == sequence_count:
                for item in sequence_items:
                    add_serial(item)
            else:
                add_error(_("Invalid group sequence: {g}").format(g=group))

        else:
            # At this point, we assume that the 'group' is just a single serial value
            add_serial(group)

    if len(errors) > 0:
        raise ValidationError(errors)

    if len(serials) == 0:
        raise ValidationError([_("No serial numbers found")])

    if len(errors) == 0 and len(serials) != expected_quantity:
        raise ValidationError([_("Number of unique serial numbers ({s}) must match quantity ({q})").format(s=len(serials), q=expected_quantity)])

    return serials


def validateFilterString(value, model=None):
    """Validate that a provided filter string looks like a list of comma-separated key=value pairs.

    These should nominally match to a valid database filter based on the model being filtered.

    e.g. "category=6, IPN=12"
    e.g. "part__name=widget"

    The ReportTemplate class uses the filter string to work out which items a given report applies to.
    For example, an acceptance test report template might only apply to stock items with a given IPN,
    so the string could be set to:

    filters = "IPN = ACME0001"

    Returns a map of key:value pairs
    """
    # Empty results map
    results = {}

    value = str(value).strip()

    if not value or len(value) == 0:
        return results

    groups = value.split(',')

    for group in groups:
        group = group.strip()

        pair = group.split('=')

        if len(pair) != 2:
            raise ValidationError(
                "Invalid group: {g}".format(g=group)
            )

        k, v = pair

        k = k.strip()
        v = v.strip()

        if not k or not v:
            raise ValidationError(
                "Invalid group: {g}".format(g=group)
            )

        results[k] = v

    # If a model is provided, verify that the provided filters can be used against it
    if model is not None:
        try:
            model.objects.filter(**results)
        except FieldError as e:
            raise ValidationError(
                str(e),
            )

    return results


def addUserPermission(user, permission):
    """Shortcut function for adding a certain permission to a user."""
    perm = Permission.objects.get(codename=permission)
    user.user_permissions.add(perm)


def addUserPermissions(user, permissions):
    """Shortcut function for adding multiple permissions to a user."""
    for permission in permissions:
        addUserPermission(user, permission)


def getMigrationFileNames(app):
    """Return a list of all migration filenames for provided app."""
    local_dir = Path(__file__).parent
    files = local_dir.joinpath('..', app, 'migrations').iterdir()

    # Regex pattern for migration files
    regex = re.compile(r"^[\d]+_.*\.py$")

    migration_files = []

    for f in files:
        if regex.match(f.name):
            migration_files.append(f.name)

    return migration_files


def getOldestMigrationFile(app, exclude_extension=True, ignore_initial=True):
    """Return the filename associated with the oldest migration."""
    oldest_num = -1
    oldest_file = None

    for f in getMigrationFileNames(app):

        if ignore_initial and f.startswith('0001_initial'):
            continue

        num = int(f.split('_')[0])

        if oldest_file is None or num < oldest_num:
            oldest_num = num
            oldest_file = f

    if exclude_extension:
        oldest_file = oldest_file.replace('.py', '')

    return oldest_file


def getNewestMigrationFile(app, exclude_extension=True):
    """Return the filename associated with the newest migration."""
    newest_file = None
    newest_num = -1

    for f in getMigrationFileNames(app):
        num = int(f.split('_')[0])

        if newest_file is None or num > newest_num:
            newest_num = num
            newest_file = f

    if exclude_extension:
        newest_file = newest_file.replace('.py', '')

    return newest_file


def clean_decimal(number):
    """Clean-up decimal value."""
    # Check if empty
    if number is None or number == '' or number == 0:
        return Decimal(0)

    # Convert to string and remove spaces
    number = str(number).replace(' ', '')

    # Guess what type of decimal and thousands separators are used
    count_comma = number.count(',')
    count_point = number.count('.')

    if count_comma == 1:
        # Comma is used as decimal separator
        if count_point > 0:
            # Points are used as thousands separators: remove them
            number = number.replace('.', '')
        # Replace decimal separator with point
        number = number.replace(',', '.')
    elif count_point == 1:
        # Point is used as decimal separator
        if count_comma > 0:
            # Commas are used as thousands separators: remove them
            number = number.replace(',', '')

    # Convert to Decimal type
    try:
        clean_number = Decimal(number)
    except InvalidOperation:
        # Number cannot be converted to Decimal (eg. a string containing letters)
        return Decimal(0)

    return clean_number.quantize(Decimal(1)) if clean_number == clean_number.to_integral() else clean_number.normalize()


def strip_html_tags(value: str, raise_error=True, field_name=None):
    """Strip HTML tags from an input string using the bleach library.

    If raise_error is True, a ValidationError will be thrown if HTML tags are detected
    """

    cleaned = clean(
        value,
        strip=True,
        tags=[],
        attributes=[],
    )

    # Add escaped characters back in
    replacements = {
        '&gt;': '>',
        '&lt;': '<',
        '&amp;': '&',
    }

    for o, r in replacements.items():
        cleaned = cleaned.replace(o, r)

    # If the length changed, it means that HTML tags were removed!
    if len(cleaned) != len(value) and raise_error:

        field = field_name or 'non_field_errors'

        raise ValidationError({
            field: [_("Remove HTML tags from this value")]
        })

    return cleaned


def remove_non_printable_characters(value: str, remove_newline=True, remove_ascii=True, remove_unicode=True):
    """Remove non-printable / control characters from the provided string"""

    cleaned = value

    if remove_ascii:
        # Remove ASCII control characters
        # Note that we do not sub out 0x0A (\n) here, it is done separately below
        cleaned = regex.sub(u'[\x01-\x09]+', '', cleaned)
        cleaned = regex.sub(u'[\x0b-\x1F]+', '', cleaned)

    if remove_newline:
        cleaned = regex.sub(u'[\x0a]+', '', cleaned)

    if remove_unicode:
        # Remove Unicode control characters
        if remove_newline:
            cleaned = regex.sub(u'[^\P{C}]+', '', cleaned)
        else:
            # Use 'negative-lookahead' to exclude newline character
            cleaned = regex.sub(u'(?![\x0A])[^\P{C}]+', '', cleaned)

    return cleaned


def hash_barcode(barcode_data):
    """Calculate a 'unique' hash for a barcode string.

    This hash is used for comparison / lookup.

    We first remove any non-printable characters from the barcode data,
    as some browsers have issues scanning characters in.
    """

    barcode_data = str(barcode_data).strip()
    barcode_data = remove_non_printable_characters(barcode_data)

    hash = hashlib.md5(str(barcode_data).encode())

    return str(hash.hexdigest())


def get_objectreference(obj, type_ref: str = 'content_type', object_ref: str = 'object_id'):
    """Lookup method for the GenericForeignKey fields.

    Attributes:
    - obj: object that will be resolved
    - type_ref: field name for the contenttype field in the model
    - object_ref: field name for the object id in the model

    Example implementation in the serializer:
    ```
    target = serializers.SerializerMethodField()
    def get_target(self, obj):
        return get_objectreference(obj, 'target_content_type', 'target_object_id')
    ```

    The method name must always be the name of the field prefixed by 'get_'
    """

    model_cls = getattr(obj, type_ref)
    obj_id = getattr(obj, object_ref)

    # check if references are set -> return nothing if not
    if model_cls is None or obj_id is None:
        return None

    # resolve referenced data into objects
    model_cls = model_cls.model_class()

    try:
        item = model_cls.objects.get(id=obj_id)
    except model_cls.DoesNotExist:
        return None

    url_fnc = getattr(item, 'get_absolute_url', None)

    # create output
    ret = {}
    if url_fnc:
        ret['link'] = url_fnc()
    return {
        'name': str(item),
        'model': str(model_cls._meta.verbose_name),
        **ret
    }


def inheritors(cls):
    """Return all classes that are subclasses from the supplied cls."""
    subcls = set()
    work = [cls]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subcls:
                subcls.add(child)
                work.append(child)
    return subcls


class InvenTreeTestCase(UserMixin, TestCase):
    """Testcase with user setup buildin."""
    pass


def notify_responsible(instance, sender, content: NotificationBody = InvenTreeNotificationBodies.NewOrder, exclude=None):
    """Notify all responsible parties of a change in an instance.

    Parses the supplied content with the provided instance and sender and sends a notification to all responsible users,
    excluding the optional excluded list.

    Args:
        instance: The newly created instance
        sender: Sender model reference
        content (NotificationBody, optional): _description_. Defaults to InvenTreeNotificationBodies.NewOrder.
        exclude (User, optional): User instance that should be excluded. Defaults to None.
    """
    if instance.responsible is not None:
        # Setup context for notification parsing
        content_context = {
            'instance': str(instance),
            'verbose_name': sender._meta.verbose_name,
            'app_label': sender._meta.app_label,
            'model_name': sender._meta.model_name,
        }

        # Setup notification context
        context = {
            'instance': instance,
            'name': content.name.format(**content_context),
            'message': content.message.format(**content_context),
            'link': InvenTree.helpers.construct_absolute_url(instance.get_absolute_url()),
            'template': {
                'html': content.template.format(**content_context),
                'subject': content.name.format(**content_context),
            }
        }

        # Create notification
        trigger_notification(
            instance,
            content.slug.format(**content_context),
            targets=[instance.responsible],
            target_exclude=[exclude],
            context=context,
        )
