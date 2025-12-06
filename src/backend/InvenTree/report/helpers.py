"""Helper functions for report generation."""

import base64
import io
import logging

from django.utils.translation import gettext_lazy as _

from common.settings import get_global_setting

logger = logging.getLogger('inventree')


def report_model_types():
    """Return a list of database models for which reports can be generated."""
    from InvenTree.helpers_model import getModelsWithMixin
    from report.mixins import InvenTreeReportMixin

    return list(getModelsWithMixin(InvenTreeReportMixin))


def report_model_from_name(model_name: str):
    """Returns the internal model class from the provided name."""
    if not model_name:
        return None

    for model in report_model_types():
        if model.__name__.lower() == model_name:
            return model


def report_model_options():
    """Return a list of options for models which support report printing."""
    return [
        (model.__name__.lower(), model._meta.verbose_name)
        for model in report_model_types()
    ]


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
    try:
        page_size = get_global_setting('REPORT_DEFAULT_PAGE_SIZE', 'A4', create=False)
    except Exception as exc:
        logger.exception('Error getting default page size: %s', exc)
        page_size = 'A4'

    return page_size


def encode_image_base64(image, img_format: str = 'PNG') -> str:
    """Return a base-64 encoded image which can be rendered in an <img> tag.

    Arguments:
        image: {Image} -- Image to encode
        img_format: {str} -- Image format (default = 'PNG')

    Returns:
        str -- Base64 encoded image data e.g. 'data:image/png;base64,xxxxxxxxx'
    """
    img_format = str(img_format).lower()

    buffered = io.BytesIO()
    image.save(buffered, img_format)

    img_str = base64.b64encode(buffered.getvalue())

    return f'data:image/{img_format};charset=utf-8;base64,' + img_str.decode()
