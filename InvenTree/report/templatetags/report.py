"""Custom template tags for report generation."""

import os

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

import InvenTree.helpers
from common.models import InvenTreeSetting
from company.models import Company
from part.models import Part
from stock.models import StockItem

register = template.Library()


@register.simple_tag()
def asset(filename):
    """Return fully-qualified path for an upload report asset file."""
    # If in debug mode, return URL to the image, not a local file
    debug_mode = InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

    if debug_mode:
        path = os.path.join(settings.MEDIA_URL, 'report', 'assets', filename)
    else:

        path = os.path.join(settings.MEDIA_ROOT, 'report', 'assets', filename)
        path = os.path.abspath(path)

        return f"file://{path}"


@register.simple_tag()
def uploaded_image(filename):
    """Return a fully-qualified path for an 'uploaded' image.

    Arguments:
        filename: The filename of the image relative to the MEDIA_ROOT directory

    Returns:
        A fully qualified path to the image
    """

    # If in debug mode, return URL to the image, not a local file
    debug_mode = InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

    # Check if the file exists
    try:
        full_path = os.path.join(settings.MEDIA_ROOT, filename)
        full_path = os.path.abspath(full_path)
        exists = os.path.exists(full_path) and os.path.isfile(full_path)
    except Exception:
        exists = False

    if debug_mode:
        # In debug mode, return a web path
        if exists:
            return os.path.join(settings.MEDIA_URL, filename)
        else:
            return os.path.join(settings.STATIC_URL, 'img', 'blank_image.png')
    else:
        # Return file path
        if exists:
            path = os.path.join(settings.MEDIA_ROOT, filename)
            path = os.path.abspath(path)
        else:
            path = os.path.join(settings.STATIC_ROOT, 'img', 'blank_image.png')
            path = os.path.abspath(path)

        return f"file://{path}"


@register.simple_tag()
def part_image(part):
    """Return a fully-qualified path for a part image."""

    if type(part) is Part:
        img = part.image.name

    elif type(part) is StockItem:
        img = part.part.image.name

    return uploaded_image(img)


@register.simple_tag()
def company_image(company):
    """Return a fully-qualified path for a company image."""

    if type(company) is Company:
        img = company.image.name
    else:
        img = ''

    return uploaded_image(img)


@register.simple_tag()
def internal_link(link, text):
    """Make a <a></a> href which points to an InvenTree URL.

    Important Note: This only works if the INVENTREE_BASE_URL parameter is set!

    If the INVENTREE_BASE_URL parameter is not configured,
    the text will be returned (unlinked)
    """
    text = str(text)

    url = InvenTree.helpers.construct_absolute_url(link)

    # If the base URL is not set, just return the text
    if not url:
        return text

    return mark_safe(f'<a href="{url}">{text}</a>')
