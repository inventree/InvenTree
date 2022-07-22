"""Custom template tags for report generation."""

import logging
import os

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

import InvenTree.helpers
from common.models import InvenTreeSetting
from company.models import Company
from part.models import Part

register = template.Library()


logger = logging.getLogger('inventree')


@register.simple_tag()
def asset(filename):
    """Return fully-qualified path for an upload report asset file.

    Arguments:
        filename: Asset filename (relative to the 'assets' media directory)

    Raises:
        FileNotFoundError if file does not exist
    """
    # If in debug mode, return URL to the image, not a local file
    debug_mode = InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

    # Test if the file actually exists
    full_path = os.path.join(settings.MEDIA_ROOT, 'report', 'assets', filename)

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise FileNotFoundError(f"Asset file '{filename}' does not exist")

    if debug_mode:
        return os.path.join(settings.MEDIA_URL, 'report', 'assets', filename)
    else:
        return f"file://{full_path}"


@register.simple_tag()
def uploaded_image(filename, replace_missing=True, replacement_file='blank_image.png'):
    """Return a fully-qualified path for an 'uploaded' image.

    Arguments:
        filename: The filename of the image relative to the MEDIA_ROOT directory
        replace_missing: Optionally return a placeholder image if the provided filename does not exist

    Returns:
        A fully qualified path to the image
    """

    # If in debug mode, return URL to the image, not a local file
    debug_mode = InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

    # Check if the file exists
    if not filename:
        exists = False
    else:
        try:
            full_path = os.path.join(settings.MEDIA_ROOT, filename)
            full_path = os.path.abspath(full_path)
            exists = os.path.exists(full_path) and os.path.isfile(full_path)
        except Exception:
            exists = False

    if exists and not InvenTree.helpers.TestIfImage(full_path):
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
            path = os.path.join(settings.MEDIA_ROOT, filename)
            path = os.path.abspath(path)
        else:
            path = os.path.join(settings.STATIC_ROOT, 'img', replacement_file)
            path = os.path.abspath(path)

        return f"file://{path}"


@register.simple_tag()
def part_image(part):
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
def logo_image():
    """Return a fully-qualified path for the logo image.

    - If a custom logo has been provided, return a path to that logo
    - Otherwise, return a path to the default InvenTree logo
    """

    # If in debug mode, return URL to the image, not a local file
    debug_mode = InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

    return InvenTree.helpers.getLogoImage(as_file=not debug_mode)


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
