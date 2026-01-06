"""Custom template tags for report generation."""

import base64
import logging
import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from django import template
from django.apps.registry import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Model
from django.db.models.query import QuerySet
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import gettext_lazy as _

from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money
from PIL import Image

import common.currency
import common.icons
import common.models
import InvenTree.helpers
import InvenTree.helpers_model
import report.helpers
from common.settings import get_global_setting
from company.models import Company
from part.models import Part

register = template.Library()


logger = logging.getLogger('inventree')


@register.simple_tag()
def order_queryset(queryset: QuerySet, *args) -> QuerySet:
    """Order a database queryset based on the provided arguments.

    Arguments:
        queryset: The queryset to order

    Keyword Arguments:
        field (str): Order the queryset based on the provided field

    Example:
        {% order_queryset companies 'name' as ordered_companies %}
    """
    if not isinstance(queryset, QuerySet):
        return queryset

    return queryset.order_by(*args)


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
def filter_db_model(model_name: str, **kwargs) -> Optional[QuerySet]:
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

    This function is provided to get around template rendering limitations.

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
def getkey(container: dict, key: str, backup_value: Optional[Any] = None) -> Any:
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
    return uploaded_image(
        InvenTree.helpers.image2name(part.image, preview, thumbnail), **kwargs
    )


@register.simple_tag()
def parameter(
    instance: Model, parameter_name: str
) -> Optional[common.models.Parameter]:
    """Return a Parameter object for the given part and parameter name.

    Arguments:
        instance: A Model object
        parameter_name: The name of the parameter to retrieve

    Returns:
        A Parameter object, or None if not found
    """
    if instance is None:
        raise ValueError('parameter tag requires a valid Model instance')

    if not isinstance(instance, Model) or not hasattr(instance, 'parameters'):
        raise TypeError("parameter tag requires a Model with 'parameters' attribute")

    return (
        instance.parameters.prefetch_related('template')
        .filter(template__name=parameter_name)
        .first()
    )


@register.simple_tag()
def part_parameter(instance, parameter_name):
    """Included for backwards compatibility - use 'parameter' tag instead.

    Ref: https://github.com/inventree/InvenTree/pull/10699
    """
    return parameter(instance, parameter_name)


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
    return uploaded_image(
        InvenTree.helpers.image2name(company.image, preview, thumbnail), **kwargs
    )


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


def make_decimal(value: Any) -> Any:
    """Convert an input value into a Decimal.

    - Converts [string, int, float] types into Decimal
    - If conversion fails, returns the original value

    The purpose of this function is to provide "seamless" math operations in templates,
    where numeric values may be provided as strings, or converted to strings during template rendering.
    """
    if any(isinstance(value, t) for t in [int, float, str]):
        try:
            value = Decimal(str(value).strip())
        except (InvalidOperation, TypeError, ValueError):
            logger.warning(
                'make_decimal: Failed to convert value to Decimal: %s (%s)',
                value,
                type(value),
            )

    return value


def cast_to_type(value: Any, cast: type) -> Any:
    """Attempt to cast a value to the provided type.

    If casting fails, the original value is returned.
    """
    if cast is not None:
        try:
            value = cast(value)
        except (ValueError, TypeError):
            pass

    return value


def debug_vars(x: Any, y: Any) -> str:
    """Return a debug string showing the types and values of two variables."""
    return f"x='{x}' ({type(x).__name__}), y='{y}' ({type(y).__name__})"


def check_nulls(func: str, *arg):
    """Check if any of the provided arguments is null.

    Raises:
        ValueError: If any argument is None
    """
    if any(a is None for a in arg):
        raise ValidationError(f'{func}: {_("Null value provided to function")}')


@register.simple_tag()
def add(x: Any, y: Any, cast: Optional[type] = None) -> Any:
    """Add two numbers (or number like values) together.

    Arguments:
        x: The first value to add
        y: The second value to add
        cast: Optional type to cast the result to (e.g. int, float, str)

    Raises:
        ValidationError: If the values cannot be added together
    """
    check_nulls('add', x, y)

    try:
        result = make_decimal(x) + make_decimal(y)
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(
            f'add: {_("Cannot add values of incompatible types")}: {debug_vars(x, y)}'
        )
    return cast_to_type(result, cast)


@register.simple_tag()
def subtract(x: Any, y: Any, cast: Optional[type] = None) -> Any:
    """Subtract one number (or number-like value) from another.

    Arguments:
        x: The value to be subtracted from
        y: The value to be subtracted
        cast: Optional type to cast the result to (e.g. int, float, str)

    Raises:
        ValidationError: If the values cannot be subtracted
    """
    check_nulls('subtract', x, y)

    try:
        result = make_decimal(x) - make_decimal(y)
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(
            f'subtract: {_("Cannot subtract values of incompatible types")}: {debug_vars(x, y)}'
        )

    return cast_to_type(result, cast)


@register.simple_tag()
def multiply(x: Any, y: Any, cast: Optional[type] = None) -> Any:
    """Multiply two numbers (or number-like values) together.

    Arguments:
        x: The first value to multiply
        y: The second value to multiply
        cast: Optional type to cast the result to (e.g. int, float, str)

    Raises:
        ValidationError: If the values cannot be multiplied together
    """
    check_nulls('multiply', x, y)

    try:
        result = make_decimal(x) * make_decimal(y)
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(
            f'multiply: {_("Cannot multiply values of incompatible types")}: {debug_vars(x, y)}'
        )

    return cast_to_type(result, cast)


@register.simple_tag()
def divide(x: Any, y: Any, cast: Optional[type] = None) -> Any:
    """Divide one number (or number-like value) by another.

    Arguments:
        x: The value to be divided
        y: The value to divide by
        cast: Optional type to cast the result to (e.g. int, float, str)

    Raises:
        ValidationError: If the values cannot be divided
    """
    check_nulls('divide', x, y)

    try:
        result = make_decimal(x) / make_decimal(y)
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(
            f'divide: {_("Cannot divide values of incompatible types")}: {debug_vars(x, y)}'
        )
    except ZeroDivisionError:
        raise ValidationError(
            f'divide: {_("Cannot divide by zero")}: {debug_vars(x, y)}'
        )

    return cast_to_type(result, cast)


@register.simple_tag()
def modulo(x: Any, y: Any, cast: Optional[type] = None) -> Any:
    """Calculate the modulo of one number (or number-like value) by another.

    Arguments:
        x: The first value to be used in the modulo operation
        y: The second value to be used in the modulo operation
        cast: Optional type to cast the result to (e.g. int, float, str)

    Raises:
        ValidationError: If the values cannot be used in a modulo operation
    """
    check_nulls('modulo', x, y)

    try:
        result = make_decimal(x) % make_decimal(y)
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(
            f'modulo: {_("Cannot perform modulo operation with values of incompatible types")} {debug_vars(x, y)}'
        )
    except ZeroDivisionError:
        raise ValidationError(
            f'modulo: {_("Cannot perform modulo operation with divisor of zero")}: {debug_vars(x, y)}'
        )

    return cast_to_type(result, cast)


@register.simple_tag
def render_currency(money, **kwargs):
    """Render a currency / Money object."""
    return InvenTree.helpers_model.render_currency(money, **kwargs)


@register.simple_tag
def create_currency(
    amount: str | int | float | Decimal, currency: Optional[str] = None, **kwargs
):
    """Create a Money object, with the provided amount and currency.

    Arguments:
        amount: The numeric amount (a numeric type or string)
        currency: The currency code (e.g. 'USD', 'EUR', etc.)

    Note: If the currency is not provided, the default system currency will be used.
    """
    check_nulls('create_currency', amount)

    currency = currency or common.currency.currency_code_default()
    currency = currency.strip().upper()

    if currency not in common.currency.CURRENCIES:
        raise ValidationError(
            f'create_currency: {_("Invalid currency code")}: {currency}'
        )

    try:
        money = Money(amount, currency)
    except InvalidOperation:
        raise ValidationError(f'create_currency: {_("Invalid amount")}: {amount}')

    return money


@register.simple_tag
def convert_currency(money: Money, currency: Optional[str] = None, **kwargs):
    """Convert a Money object to the specified currency.

    Arguments:
        money: The Money instance to be converted
        currency: The target currency code (e.g. 'USD', 'EUR', etc.)

    Note: If the currency is not provided, the default system currency will be used.
    """
    check_nulls('convert_currency', money)

    if not isinstance(money, Money):
        raise TypeError('convert_currency tag requires a Money instance')

    currency = currency or common.currency.currency_code_default()
    currency = currency.strip().upper()

    if currency not in common.currency.CURRENCIES:
        raise ValidationError(
            f'convert_currency: {_("Invalid currency code")}: {currency}'
        )

    try:
        converted = convert_money(money, currency)
    except MissingRate:
        # Re-throw error with more context
        raise ValidationError(
            f'convert_currency: {_("Missing exchange rate")} {money.currency} -> {currency}'
        )

    return converted


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
    number: int | float | Decimal,
    decimal_places: Optional[int] = None,
    multiplier: Optional[int | float | Decimal] = None,
    integer: bool = False,
    leading: int = 0,
    separator: Optional[str] = None,
) -> str:
    """Render a number with optional formatting options.

    Arguments:
        number: The number to be formatted
        decimal_places: Number of decimal places to render
        multiplier: Optional multiplier to apply to the number before formatting
        integer: Boolean, whether to render the number as an integer
        leading: Number of leading zeros (default = 0)
        separator: Character to use as a thousands separator (default = None)
    """
    check_nulls('format_number', number)

    try:
        number = Decimal(str(number).strip())
    except Exception:
        # If the number cannot be converted to a Decimal, just return the original value
        return str(number)

    if multiplier is not None:
        number *= Decimal(str(multiplier).strip())

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
    # Ensure that the output never uses scientific notation
    value = Decimal(number)
    value = (
        value.quantize(Decimal(1))
        if value == value.to_integral()
        else value.normalize()
    )

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
    check_nulls('format_datetime', dt)

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
    check_nulls('format_date', dt)

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
