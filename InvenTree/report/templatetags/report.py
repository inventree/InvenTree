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

        path = settings.MEDIA_ROOT.joinpath('report', 'assets', filename).absolute()

        return f"file://{path}"


@register.simple_tag()
def part_image(part):
    """Return a fully-qualified path for a part image."""
    # If in debug mode, return URL to the image, not a local file
    debug_mode = InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

    if type(part) is Part:
        img = part.image.name

    elif type(part) is StockItem:
        img = part.part.image.name

    else:
        img = ''

    if debug_mode:
        if img:
            return os.path.join(settings.MEDIA_URL, img)
        else:
            return os.path.join(settings.STATIC_URL, 'img', 'blank_image.png')

    else:
        path = settings.MEDIA_ROOT.joinpath(img).absolute()

        if not path.exists() or not path.is_file():
            # Image does not exist
            # Return the 'blank' image
            path = settings.STATIC_ROOT.joinpath('img', 'blank_image.png').absolute()

        return f"file://{path}"


@register.simple_tag()
def company_image(company):
    """Return a fully-qualified path for a company image."""
    # If in debug mode, return the URL to the image, not a local file
    debug_mode = InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

    if type(company) is Company:
        img = company.image.name
    else:
        img = ''

    if debug_mode:
        if img:
            return os.path.join(settings.MEDIA_URL, img)
        else:
            return os.path.join(settings.STATIC_URL, 'img', 'blank_image.png')

    else:
        path = settings.MEDIA_ROOT.joinpath(img).absolute()

        if not path.exists() or not path.is_file():
            # Image does not exist
            # Return the 'blank' image
            path = settings.STATIC_ROOT.joinpath('img', 'blank_image.png').absolute()

        return f"file://{path}"


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
