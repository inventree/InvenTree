"""
Provides helper functions used throughout the InvenTree project
"""

import io
import re
import json
import os.path
from PIL import Image

from decimal import Decimal

from wsgiref.util import FileWrapper
from django.http import StreamingHttpResponse
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from .version import inventreeVersion, inventreeInstanceName
from .settings import MEDIA_URL, STATIC_URL


def generateTestKey(test_name):
    """
    Generate a test 'key' for a given test name.
    This must not have illegal chars as it will be used for dict lookup in a template.
    
    Tests must be named such that they will have unique keys.
    """

    key = test_name.strip().lower()
    key = key.replace(" ", "")

    # Remove any characters that cannot be used to represent a variable
    key = re.sub(r'[^a-zA-Z0-9]', '', key)

    return key


def getMediaUrl(filename):
    """
    Return the qualified access path for the given file,
    under the media directory.
    """

    return os.path.join(MEDIA_URL, str(filename))


def getStaticUrl(filename):
    """
    Return the qualified access path for the given file,
    under the static media directory.
    """

    return os.path.join(STATIC_URL, str(filename))


def getBlankImage():
    """
    Return the qualified path for the 'blank image' placeholder.
    """

    return getStaticUrl("img/blank_image.png")


def getBlankThumbnail():
    """
    Return the qualified path for the 'blank image' thumbnail placeholder.
    """

    return getStaticUrl("img/blank_image.thumbnail.png")


def TestIfImage(img):
    """ Test if an image file is indeed an image """
    try:
        Image.open(img).verify()
        return True
    except:
        return False


def TestIfImageURL(url):
    """ Test if an image URL (or filename) looks like a valid image format.

    Simply tests the extension against a set of allowed values
    """
    return os.path.splitext(os.path.basename(url))[-1].lower() in [
        '.jpg', '.jpeg',
        '.png', '.bmp',
        '.tif', '.tiff',
        '.webp', '.gif',
    ]
        

def str2bool(text, test=True):
    """ Test if a string 'looks' like a boolean value.

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


def isNull(text):
    """
    Test if a string 'looks' like a null value.
    This is useful for querying the API against a null key.
    
    Args:
        text: Input text
    
    Returns:
        True if the text looks like a null value
    """

    return str(text).strip().lower() in ['top', 'null', 'none', 'empty', 'false', '-1', '']


def normalize(d):
    """
    Normalize a decimal number, and remove exponential formatting.
    """

    if type(d) is not Decimal:
        d = Decimal(d)

    d = d.normalize()
    
    # Ref: https://docs.python.org/3/library/decimal.html
    return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()


def increment(n):
    """
    Attempt to increment an integer (or a string that looks like an integer!)
    
    e.g.

    001 -> 002
    2 -> 3
    AB01 -> AB02
    QQQ -> QQQ
    
    """

    value = str(n).strip()

    # Ignore empty strings
    if not value:
        return value

    pattern = r"(.*?)(\d+)?$"

    result = re.search(pattern, value)

    # No match!
    if result is None:
        return value

    groups = result.groups()

    # If we cannot match the regex, then simply return the provided value
    if not len(groups) == 2:
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
    """
    Format a Decimal number as a string,
    stripping out any trailing zeroes or decimal points.
    Essentially make it look like a whole number if it is one.

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


def WrapWithQuotes(text, quote='"'):
    """ Wrap the supplied text with quotes

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


def MakeBarcode(object_name, object_pk, object_data, **kwargs):
    """ Generate a string for a barcode. Adds some global InvenTree parameters.

    Args:
        object_type: string describing the object type e.g. 'StockItem'
        object_id: ID (Primary Key) of the object in the database
        object_url: url for JSON API detail view of the object
        data: Python dict object containing extra datawhich will be rendered to string (must only contain stringable values)

    Returns:
        json string of the supplied data plus some other data
    """

    brief = kwargs.get('brief', False)

    data = {}

    if brief:
        data[object_name] = object_pk
    else:
        data['tool'] = 'InvenTree'
        data['version'] = inventreeVersion()
        data['instance'] = inventreeInstanceName()

        # Ensure PK is included
        object_data['id'] = object_pk
        data[object_name] = object_data

    return json.dumps(data, sort_keys=True)


def GetExportFormats():
    """ Return a list of allowable file formats for exporting data """
    
    return [
        'csv',
        'tsv',
        'xls',
        'xlsx',
        'json',
        'yaml',
    ]


def DownloadFile(data, filename, content_type='application/text'):
    """ Create a dynamic file for the user to download.
    
    Args:
        data: Raw file data (string or bytes)
        filename: Filename for the file download
        content_type: Content type for the download

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
    response['Content-Disposition'] = 'attachment; filename={f}'.format(f=filename)

    return response


def ExtractSerialNumbers(serials, expected_quantity):
    """ Attempt to extract serial numbers from an input string.
    - Serial numbers must be integer values
    - Serial numbers must be positive
    - Serial numbers can be split by whitespace / newline / commma chars
    - Serial numbers can be supplied as an inclusive range using hyphen char e.g. 10-20

    Args:
        expected_quantity: The number of (unique) serial numbers we expect
    """

    serials = serials.strip()

    groups = re.split("[\s,]+", serials)

    numbers = []
    errors = []

    try:
        expected_quantity = int(expected_quantity)
    except ValueError:
        raise ValidationError([_("Invalid quantity provided")])

    if len(serials) == 0:
        raise ValidationError([_("Empty serial number string")])

    for group in groups:

        group = group.strip()

        # Hyphen indicates a range of numbers
        if '-' in group:
            items = group.split('-')

            if len(items) == 2:
                a = items[0].strip()
                b = items[1].strip()

                try:
                    a = int(a)
                    b = int(b)

                    if a < b:
                        for n in range(a, b + 1):
                            if n in numbers:
                                errors.append(_('Duplicate serial: {n}'.format(n=n)))
                            else:
                                numbers.append(n)
                    else:
                        errors.append(_("Invalid group: {g}".format(g=group)))

                except ValueError:
                    errors.append(_("Invalid group: {g}".format(g=group)))
                    continue
            else:
                errors.append(_("Invalid group: {g}".format(g=group)))
                continue

        else:
            if group in numbers:
                errors.append(_("Duplicate serial: {g}".format(g=group)))
            else:
                numbers.append(group)

    if len(errors) > 0:
        raise ValidationError(errors)

    if len(numbers) == 0:
        raise ValidationError([_("No serial numbers found")])

    # The number of extracted serial numbers must match the expected quantity
    if not expected_quantity == len(numbers):
        raise ValidationError([_("Number of unique serial number ({s}) must match quantity ({q})".format(s=len(numbers), q=expected_quantity))])

    return numbers


def validateFilterString(value):
    """
    Validate that a provided filter string looks like a list of comma-separated key=value pairs

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

        if not len(pair) == 2:
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

    return results
