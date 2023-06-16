"""Custom template tags for report generation."""

import base64
import logging
import os

from django import template
from django.conf import settings
from django.utils.safestring import SafeString, mark_safe

import InvenTree.helpers
import InvenTree.helpers_model
from common.models import InvenTreeSetting
from company.models import Company
from part.models import Part

register = template.Library()


logger = logging.getLogger('inventree')


@register.simple_tag()
def getindex(container: list, index: int):
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

    try:
        value = container[index]
    except IndexError:
        value = None

    return value


@register.simple_tag()
def getkey(container: dict, key):
    """Perform key lookup in the provided dict object.

    This function is provided to get around template rendering limitations.
    Ref: https://stackoverflow.com/questions/1906129/dict-keys-with-spaces-in-django-templates

    Arguments:
        container: A python dict object
        key: The 'key' to be found within the dict
    """
    if type(container) is not dict:
        logger.warning("getkey() called with non-dict object")
        return None

    if key in container:
        return container[key]
    else:
        return None


@register.simple_tag()
def asset(filename):
    """Return fully-qualified path for an upload report asset file.

    Arguments:
        filename: Asset filename (relative to the 'assets' media directory)

    Raises:
        FileNotFoundError if file does not exist
    """
    if type(filename) is SafeString:
        # Prepend an empty string to enforce 'stringiness'
        filename = '' + filename

    # If in debug mode, return URL to the image, not a local file
    debug_mode = InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

    # Test if the file actually exists
    full_path = settings.MEDIA_ROOT.joinpath('report', 'assets', filename).resolve()

    if not full_path.exists() or not full_path.is_file():
        raise FileNotFoundError(f"Asset file '{filename}' does not exist")

    if debug_mode:
        return os.path.join(settings.MEDIA_URL, 'report', 'assets', filename)
    else:
        return f"file://{full_path}"


@register.simple_tag()
def uploaded_image(filename, replace_missing=True, replacement_file='blank_image.png', validate=True):
    """Return a fully-qualified path for an 'uploaded' image.

    Arguments:
        filename: The filename of the image relative to the MEDIA_ROOT directory
        replace_missing: Optionally return a placeholder image if the provided filename does not exist
        validate: Optionally validate that the file is a valid image file (default = True)

    Returns:
        A fully qualified path to the image
    """

    if type(filename) is SafeString:
        # Prepend an empty string to enforce 'stringiness'
        filename = '' + filename

    # If in debug mode, return URL to the image, not a local file
    debug_mode = InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

    # Check if the file exists
    if not filename:
        exists = False
    else:
        try:
            full_path = settings.MEDIA_ROOT.joinpath(filename).resolve()
            exists = full_path.exists() and full_path.is_file()
        except Exception:
            exists = False

    if exists and validate and not InvenTree.helpers.TestIfImage(full_path):
        logger.warning(f"File '{filename}' is not a valid image")
        exists = False

    if not exists and not replace_missing:
        raise FileNotFoundError(f"Image file '{filename}' not found")

    if debug_mode:
        # In debug mode, return a web path
        if exists:
            return os.path.join(settings.MEDIA_URL, filename)
        else:
            return os.path.join(settings.STATIC_URL, 'img', replacement_file)
    else:
        # Return file path
        if exists:
            path = settings.MEDIA_ROOT.joinpath(filename).resolve()
        else:
            path = settings.STATIC_ROOT.joinpath('img', replacement_file).resolve()

        return f"file://{path}"


@register.simple_tag()
def encode_svg_image(filename):
    """Return a base64-encoded svg image data string"""

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
        raise FileNotFoundError(f"Image file '{filename}' not found")

    # Read the file data
    with open(full_path, 'rb') as f:
        data = f.read()

    # Return the base64-encoded data
    return "data:image/svg+xml;charset=utf-8;base64," + base64.b64encode(data).decode('utf-8')


@register.simple_tag()
def part_image(part: Part):
    """Return a fully-qualified path for a part image.

    Arguments:
        part: a Part model instance

    Raises:
        TypeError if provided part is not a Part instance
    """

    if type(part) is Part:
        img = part.image.name

    else:
        raise TypeError("part_image tag requires a Part instance")

    return uploaded_image(img)


@register.simple_tag()
def part_parameter(part: Part, parameter_name: str):
    """Return a PartParameter object for the given part and parameter name

    Arguments:
        part: A Part object
        parameter_name: The name of the parameter to retrieve

    Returns:
        A PartParameter object, or None if not found
    """
    if type(part) is Part:
        return part.get_parameter(parameter_name)
    else:
        return None


@register.simple_tag()
def company_image(company):
    """Return a fully-qualified path for a company image.

    Arguments:
        company: a Company model instance

    Raises:
        TypeError if provided company is not a Company instance
    """

    if type(company) is Company:
        img = company.image.name
    else:
        raise TypeError("company_image tag requires a Company instance")

    return uploaded_image(img)


@register.simple_tag()
def logo_image(**kwargs):
    """Return a fully-qualified path for the logo image.

    - If a custom logo has been provided, return a path to that logo
    - Otherwise, return a path to the default InvenTree logo
    """

    # If in debug mode, return URL to the image, not a local file
    debug_mode = InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

    return InvenTree.helpers.getLogoImage(as_file=not debug_mode, **kwargs)


@register.simple_tag()
def internal_link(link, text):
    """Make a <a></a> href which points to an InvenTree URL.

    Uses the InvenTree.helpers_model.construct_absolute_url function to build the URL.
    """
    text = str(text)

    url = InvenTree.helpers_model.construct_absolute_url(link)

    # If the base URL is not set, just return the text
    if not url:
        return text

    return mark_safe(f'<a href="{url}">{text}</a>')


@register.simple_tag()
def add(x, y, *args, **kwargs):
    """Add two numbers together."""
    return x + y


@register.simple_tag()
def subtract(x, y):
    """Subtract one number from another"""
    return x - y


@register.simple_tag()
def multiply(x, y):
    """Multiply two numbers together"""
    return x * y


@register.simple_tag()
def divide(x, y):
    """Divide one number by another"""
    return x / y


@register.simple_tag
def render_currency(money, **kwargs):
    """Render a currency / Money object"""

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

    if kwargs.get('bold', False):
        tags.append('strong')

    if kwargs.get('italic', False):
        tags.append('em')

    if heading := kwargs.get('heading', ''):
        tags.append(heading)

    output = ''.join([f'<{tag}>' for tag in tags])
    output += text
    output += ''.join([f'</{tag}>' for tag in tags])

    return mark_safe(output)
