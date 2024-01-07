"""Helper functions for report generation."""

import base64
import io
import logging

from django.utils.translation import gettext_lazy as _

logger = logging.getLogger('inventree')


def report_page_size_options():
    """Returns a list of page size options for PDF reports."""
    return [
        ('A4', _('A4')),
        ('A3', _('A3')),
        ('Legal', _('Legal')),
        ('Letter', _('Letter')),
    ]


def page_sizes():
    """Returns a dict of page sizes for PDF reports."""
    return {
        'A4': (210, 297),
        'A3': (297, 420),
        'Legal': (215.9, 355.6),
        'Letter': (215.9, 279.4),
    }


def page_size(page_code):
    """Return the page size associated with a particular page code."""
    if page_code in page_sizes():
        return page_sizes()[page_code]

    # Default to A4
    logger.warning("Unknown page size code '%s' - defaulting to A4", page_code)
    return page_sizes()['A4']


def report_page_size_default():
    """Returns the default page size for PDF reports."""
    from common.models import InvenTreeSetting

    try:
        page_size = InvenTreeSetting.get_setting('REPORT_DEFAULT_PAGE_SIZE', 'A4')
    except Exception as exc:
        logger.exception('Error getting default page size: %s', str(exc))
        page_size = 'A4'

    return page_size


def encode_image_base64(image, format: str = 'PNG'):
    """Return a base-64 encoded image which can be rendered in an <img> tag.

    Arguments:
        image {Image} -- Image object
        format {str} -- Image format (e.g. 'PNG')

    Returns:
        str -- Base64 encoded image data e.g. 'data:image/png;base64,xxxxxxxxx'
    """
    fmt = format.lower()

    buffered = io.BytesIO()
    image.save(buffered, fmt)

    img_str = base64.b64encode(buffered.getvalue())

    return f'data:image/{fmt};charset=utf-8;base64,' + img_str.decode()
