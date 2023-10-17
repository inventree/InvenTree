"""Helper functions for report generation."""

import logging

from django.utils.translation import gettext_lazy as _

logger = logging.getLogger('inventree')


def report_page_size_options():
    """Returns a list of page size options for PDF reports."""
    return [
        ('A4', _('A4')),
        ('Legal', _('Legal')),
        ('Letter', _('Letter')),
    ]


def report_page_size_default():
    """Returns the default page size for PDF reports."""
    from common.models import InvenTreeSetting

    try:
        page_size = InvenTreeSetting.get_setting('REPORT_DEFAULT_PAGE_SIZE', 'A4')
    except Exception as exc:
        logger.exception("Error getting default page size: %s", str(exc))
        page_size = 'A4'

    return page_size
