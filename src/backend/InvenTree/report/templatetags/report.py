"""Custom template tags for report generation."""

import base64
import logging
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from django import template
from django.apps.registry import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import gettext_lazy as _

from PIL import Image

import common.icons
import InvenTree.helpers
import InvenTree.helpers_model
import report.helpers
from common.settings import get_global_setting
from company.models import Company
from part.models import Part

register = template.Library()


logger = logging.getLogger('inventree')


@register.simple_tag()
def filter_queryset(queryset: QuerySet, **kwargs) -> QuerySet:
    """Filter a database queryset based on the provided keyword arguments.

    Arguments:
        queryset: The queryset to filter

    Keyword Arguments:
        field (any): Filter the queryset based on the provided field

    Example:
        {% filter_queryset companies is_supplier=True as suppliers %}
    """
    if not isinstance(queryset, QuerySet):
        return queryset
    return queryset.filter(**kwargs)


@register.simple_tag()
def filter_db_model(model_name: str, **kwargs) -> QuerySet:
    """Filter a database model based on the provided keyword arguments.

    Arguments:
        model_name: The name of the Django model - including app name (e.g. 'part.partcategory')

    Keyword Arguments:
        field (any): Filter the queryset based on the provided field

    Example:
        {% filter_db_model 'part.partcategory' is_template=True as template_parts %}
    """
    try:
        app_name, model_name = model_name.split('.')
    except ValueError:
        return None

    try:
        model = apps.get_model(app_name, model_name)
    except Exception:
        return None

    if model is None:
        return None

    queryset = model.objects.all()

    return filter_queryset(queryset, **kwargs)


@register.simple_tag()
def getindex(container: list, index: int) -> Any:
    """Return the value contained at the specified index of the list.

    This function is provideed to get around template rendering limitations.

    Arguments:
        container: A python list object
        index: The index to retrieve from the list
    """
    # Index *must* be an integer
    try:
        index = int(index)
    except ValueError:
        return None

    if index < 0 or index >= len(container):
        return None
    return container[index]


@register.simple_tag()
def getkey(container: dict, key: str, backup_value: Optional[any] = None) -> Any:
    """Perform key lookup in the provided dict object.

    This function is provided to get around template rendering limitations.
    Ref: https://stackoverflow.com/questions/1906129/dict-keys-with-spaces-in-django-templates

    Arguments:
        container: A python dict object
        key: The 'key' to be found within the dict
        backup_value: A backup value to return if the key is not found
    """
    if type(container) is not dict:
        logger.warning('getkey() called with non-dict object')
        return None

    return container.get(key, backup_value)


@register.simple_tag()
def asset(filename):
    """Return fully-qualified path for an upload report asset file.

    Arguments:
        filename: Asset filename (relative to the 'assets' media directory)

    Raises:
        FileNotFoundError: If file does not exist
    """
    if type(filename) is SafeString:
        # Prepend an empty string to enforce 'stringiness'
        filename = '' + filename

    # If in debug mode, return URL to the image, not a local file
    debug_mode = get_global_setting('REPORT_DEBUG_MODE', cache=False)

    # Test if the file actually exists
    full_path = settings.MEDIA_ROOT.joinpath('report', 'assets', filename).resolve()

    if not full_path.exists() or not full_path.is_file():
        raise FileNotFoundError(_('Asset file does not exist') + f": '{filename}'")

    if debug_mode:
        return os.path.join(settings.MEDIA_URL, 'report', 'assets', filename)
    return f'file://{full_path}'


@register.simple_tag()
def uploaded_image(
    filename: str,
    replace_missing: bool = True,
    replacement_file: str = 'blank_image.png',
    validate: bool = True,
    width: Optional[int] = None,
    height: Optional[int] = None,
    rotate: Optional[float] = None,
    **kwargs,
) -> str:
    """Return raw image data from an 'uploaded' image.

    Arguments:
        filename: The filename of the image relative to the MEDIA_ROOT directory
        replace_missing: Optionally return a placeholder image if the provided filename does not exist (default = True)
        replacement_file: The filename of the placeholder image (default = 'blank_image.png')
        validate: Optionally validate that the file is a valid image file
        width: Optional width of the image
        height: Optional height of the image
        rotate: Optional rotation to apply to the image

    Returns:
        Binary image data to be rendered directly in a <img> tag

    Raises:
        FileNotFoundError: If the file does not exist
    """
    if type(filename) is SafeString:
        # Prepend an empty string to enforce 'stringiness'
        filename = '' + filename

    # If in debug mode, return URL to the image, not a local file
    debug_mode = get_global_setting('REPORT_DEBUG_MODE', cache=False)

    # Check if the file exists
    if not filename:
        exists = False
    else:
        try:
            full_path = settings.MEDIA_ROOT.joinpath(filename).resolve()
            exists = full_path.exists() and full_path.is_file()
        except Exception:  # pragma: no cover
            exists = False  # pragma: no cover

    if exists and validate and not InvenTree.helpers.TestIfImage(full_path):
        logger.warning("File '%s' is not a valid image", filename)
        exists = False

    if not exists and not replace_missing:
        raise FileNotFoundError(_('Image file not found') + f": '{filename}'")

    if debug_mode:
        # In debug mode, return a web path (rather than an encoded image blob)
        if exists:
            return os.path.join(settings.MEDIA_URL, filename)
        return os.path.join(settings.STATIC_URL, 'img', replacement_file)

    elif not exists:
        full_path = settings.STATIC_ROOT.joinpath('img', replacement_file).resolve()

    # Load the image, check that it is valid
    if full_path.exists() and full_path.is_file():
        img = Image.open(full_path)
    else:
        # A placeholder image showing that the image is missing
        img = Image.new('RGB', (64, 64), color='red')

    if width is not None:
        try:
            width = int(width)
        except ValueError:
            width = None

    if height is not None:
        try:
            height = int(height)
        except ValueError:
            height = None

    if width is not None and height is not None:
        # Resize the image, width *and* height are provided
        img = img.resize((width, height))
    elif width is not None:
        # Resize the image, width only
        wpercent = width / float(img.size[0])
        hsize = int(float(img.size[1]) * float(wpercent))
        img = img.resize((width, hsize))
    elif height is not None:
        # Resize the image, height only
        hpercent = height / float(img.size[1])
        wsize = int(float(img.size[0]) * float(hpercent))
        img = img.resize((wsize, height))

    # Optionally rotate the image
    if rotate is not None:
        try:
            rotate = int(rotate)
            img = img.rotate(rotate)
        except ValueError:
            pass

    # Return a base-64 encoded image
    img_data = report.helpers.encode_image_base64(img)

    return img_data


@register.simple_tag()
def encode_svg_image(filename: str) -> str:
    """Return a base64-encoded svg image data string."""
    if type(filename) is SafeString:
        # Prepend an empty string to enforce 'stringiness'
        filename = '' + filename

    # Check if the file exists
    if not filename:
        exists = False
    else:
        try:
            full_path = settings.MEDIA_ROOT.joinpath(filename).resolve()
            exists = full_path.exists() and full_path.is_file()
        except Exception:
            exists = False

    if not exists:
        raise FileNotFoundError(_('Image file not found') + f": '{filename}'")

    # Read the file data
    with open(full_path, 'rb') as f:
        data = f.read()

    # Return the base64-encoded data
    return 'data:image/svg+xml;charset=utf-8;base64,' + base64.b64encode(data).decode(
        'utf-8'
    )


@register.simple_tag()
def part_image(part: Part, preview: bool = False, thumbnail: bool = False, **kwargs):
    """Return a fully-qualified path for a part image.

    Arguments:
        part: A Part model instance
        preview: Return the preview image (default = False)
        thumbnail: Return the thumbnail image (default = False)

    Raises:
        TypeError: If provided part is not a Part instance
    """
    if type(part) is not Part:
        raise TypeError(_('part_image tag requires a Part instance'))

    if not part.image:
        img = None
    elif preview:
        img = None if not hasattr(part.image, 'preview') else part.image.preview.name
    elif thumbnail:
        img = (
            None if not hasattr(part.image, 'thumbnail') else part.image.thumbnail.name
        )
    else:
        img = part.image.name

    return uploaded_image(img, **kwargs)


@register.simple_tag()
def part_parameter(part: Part, parameter_name: str) -> str:
    """Return a PartParameter object for the given part and parameter name.

    Arguments:
        part: A Part object
        parameter_name: The name of the parameter to retrieve

    Returns:
        A PartParameter object, or None if not found
    """
    if type(part) is Part:
        return part.get_parameter(parameter_name)
    return None


@register.simple_tag()
def company_image(
    company: Company, preview: bool = False, thumbnail: bool = False, **kwargs
) -> str:
    """Return a fully-qualified path for a company image.

    Arguments:
        company: A Company model instance
        preview: Return the preview image (default = False)
        thumbnail: Return the thumbnail image (default = False)

    Raises:
        TypeError: If provided company is not a Company instance
    """
    if type(company) is not Company:
        raise TypeError(_('company_image tag requires a Company instance'))

    if preview:
        img = company.image.preview.name
    elif thumbnail:
        img = company.image.thumbnail.name
    else:
        img = company.image.name

    return uploaded_image(img, **kwargs)


@register.simple_tag()
def logo_image(**kwargs) -> str:
    """Return a fully-qualified path for the logo image.

    - If a custom logo has been provided, return a path to that logo
    - Otherwise, return a path to the default InvenTree logo
    """
    # If in debug mode, return URL to the image, not a local file
    debug_mode = get_global_setting('REPORT_DEBUG_MODE', cache=False)

    return InvenTree.helpers.getLogoImage(as_file=not debug_mode, **kwargs)


@register.simple_tag()
def internal_link(link, text) -> str:
    """Make a <a></a> href which points to an InvenTree URL.

    Uses the InvenTree.helpers_model.construct_absolute_url function to build the URL.
    """
    text = str(text)

    try:
        url = InvenTree.helpers_model.construct_absolute_url(link)
    except Exception:
        url = None

    # If the base URL is not set, just return the text
    if not url:
        logger.warning('Failed to construct absolute URL for internal link')
        return text

    return mark_safe(f'<a href="{url}">{text}</a>')


@register.simple_tag()
def add(x, y, *args, **kwargs):
    """Add two numbers together."""
    return x + y


@register.simple_tag()
def subtract(x, y):
    """Subtract one number from another."""
    return x - y


@register.simple_tag()
def multiply(x, y):
    """Multiply two numbers together."""
    return x * y


@register.simple_tag()
def divide(x, y):
    """Divide one number by another."""
    return x / y


@register.simple_tag
def render_currency(money, **kwargs):
    """Render a currency / Money object."""
    return InvenTree.helpers_model.render_currency(money, **kwargs)


@register.simple_tag
def render_html_text(text: str, **kwargs):
    """Render a text item with some simple html tags.

    kwargs:
        bold: Boolean, whether bold (or not)
        italic: Boolean, whether italic (or not)
        heading: str, heading level e.g. 'h3'
    """
    tags = []

    if kwargs.get('bold'):
        tags.append('strong')

    if kwargs.get('italic'):
        tags.append('em')

    if heading := kwargs.get('heading', ''):
        tags.append(heading)

    output = ''.join([f'<{tag}>' for tag in tags])
    output += text
    output += ''.join([f'</{tag}>' for tag in tags])

    return mark_safe(output)


@register.simple_tag
def format_number(
    number,
    decimal_places: Optional[int] = None,
    integer: bool = False,
    leading: int = 0,
    separator: Optional[str] = None,
) -> str:
    """Render a number with optional formatting options.

    Arguments:
        decimal_places: Number of decimal places to render
        integer: Boolean, whether to render the number as an integer
        leading: Number of leading zeros (default = 0)
        separator: Character to use as a thousands separator (default = None)
    """
    try:
        number = Decimal(str(number))
    except Exception:
        # If the number cannot be converted to a Decimal, just return the original value
        return str(number)

    if integer:
        # Convert to integer
        number = Decimal(int(number))

    # Normalize the number (remove trailing zeroes)
    number = number.normalize()

    if decimal_places is not None:
        try:
            decimal_places = int(decimal_places)
            number = round(number, decimal_places)
        except ValueError:
            pass

    # Re-encode, and normalize again
    value = Decimal(number).normalize()

    if separator:
        value = f'{value:,}'
        value = value.replace(',', separator)
    else:
        value = f'{value}'

    if leading is not None:
        try:
            leading = int(leading)
            value = '0' * leading + value
        except ValueError:
            pass

    return value


@register.simple_tag
def format_datetime(
    dt: datetime, timezone: Optional[str] = None, fmt: Optional[str] = None
):
    """Format a datetime object for display.

    Arguments:
        dt: The datetime object to format
        timezone: The timezone to use for the date (defaults to the server timezone)
        fmt: The format string to use (defaults to ISO formatting)
    """
    dt = InvenTree.helpers.to_local_time(dt, timezone)

    if fmt:
        return dt.strftime(fmt)
    else:
        return dt.isoformat()


@register.simple_tag
def format_date(dt: date, timezone: Optional[str] = None, fmt: Optional[str] = None):
    """Format a date object for display.

    Arguments:
        dt: The date to format
        timezone: The timezone to use for the date (defaults to the server timezone)
        fmt: The format string to use (defaults to ISO formatting)
    """
    try:
        dt = InvenTree.helpers.to_local_time(dt, timezone).date()
    except TypeError:
        return str(dt)

    if fmt:
        return dt.strftime(fmt)
    else:
        return dt.isoformat()


@register.simple_tag()
def icon(name, **kwargs):
    """Render an icon from the icon packs.

    Arguments:
        name: The name of the icon to render

    Keyword Arguments:
        class: Optional class name(s) to apply to the icon element
    """
    if not name:
        return ''

    try:
        pack, icon, variant = common.icons.validate_icon(name)
    except ValidationError:
        return ''

    unicode = chr(int(icon['variants'][variant], 16))
    return mark_safe(
        f'<i class="icon {kwargs.get("class", "")}" style="font-family: inventree-icon-font-{pack.prefix}">{unicode}</i>'
    )


@register.simple_tag()
def include_icon_fonts(ttf: bool = False, woff: bool = False):
    """Return the CSS font-face rule for the icon fonts used on the current page (or all)."""
    fonts = []

    if not ttf and not woff:
        ttf = woff = True

    for font in common.icons.get_icon_packs().values():
        # generate the font src string (prefer ttf over woff, woff2 is not supported by weasyprint)
        if 'truetype' in font.fonts and ttf:
            font_format, url = 'truetype', font.fonts['truetype']
        elif 'woff' in font.fonts and woff:
            font_format, url = 'woff', font.fonts['woff']

        fonts.append(f"""
@font-face {'{'}
    font-family: 'inventree-icon-font-{font.prefix}';
    src: url('{InvenTree.helpers_model.construct_absolute_url(url)}') format('{font_format}');
{'}'}\n""")

    icon_class = f"""
.icon {'{'}
    font-style: normal;
    font-weight: normal;
    font-variant: normal;
    text-transform: none;
    line-height: 1;
    /* Better font rendering */
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
{'}'}
    """

    return mark_safe(icon_class + '\n'.join(fonts))
