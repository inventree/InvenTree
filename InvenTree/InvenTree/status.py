"""
Provides system status functionality checks.
"""
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta

from django.utils.translation import ugettext as _

from django_q.models import Success
from django_q.monitor import Stat

logger = logging.getLogger(__name__)


def is_q_cluster_running(**kwargs):
    """
    Return True if at least one cluster worker is running
    """

    clusters = Stat.get_all()

    if len(clusters) > 0:
        return True

    """
    Sometimes Stat.get_all() returns [].
    In this case we have the 'heartbeat' task running every five minutes.
    Check to see if we have a result within the last ten minutes
    """

    now = datetime.now()
    past = now - timedelta(minutes=10)

    results = Success.objects.filter(
        func='InvenTree.tasks.heartbeat',
        started__gte=past
    )

    # If any results are returned, then the background worker is running!
    return results.exists()


def check_system_health(**kwargs):
    """
    Check that the InvenTree system is running OK.

    Returns True if all system checks pass.
    """

    result = True

    if not is_q_cluster_running(**kwargs):
        result = False
        logger.warning(_("Celery worker check failed"))

    if not result:
        logger.warning(_("InvenTree system health checks failed"))

    return result
