"""
Provides system status functionality checks.
"""

from django.utils.translation import ugettext as _

import logging


logger = logging.getLogger(__name__)


def check_system_health(**kwargs):
    """
    Check that the InvenTree system is running OK.

    Returns True if all system checks pass.
    """

    result = True

    if not check_celery_worker(**kwargs):
        result = False
        logger.warning(_("Celery worker check failed"))

    if not result:
        logger.warning(_("InvenTree system health checks failed"))

    return result


def check_celery_worker(**kwargs):
    """
    Check that a celery worker is running.
    """

    # TODO - Checks that the configured celery worker thing is running

    return True
