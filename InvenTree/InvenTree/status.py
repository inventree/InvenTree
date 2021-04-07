"""
Provides system status functionality checks.
"""
# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

import logging
from datetime import datetime, timedelta

from django_q.models import Success
from django_q.monitor import Stat

logger = logging.getLogger(__name__)


def is_q_cluster_running(**kwargs):
    """
    Return True if at least one cluster worker is running
    """

    clusters = Stat.get_all()

    if len(clusters) > 0:
        # TODO - Introspect on any cluster information
        return True

    """
    Sometimes Stat.get_all() returns [].
    In this case we have the 'heartbeat' task running every 15 minutes.
    Check to see if we have a result within the last 20 minutes
    """

    now = datetime.now()
    past = now - timedelta(minutes=20)

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
        logger.warning(_("Background worker check failed"))

    if not result:
        logger.warning(_("InvenTree system health checks failed"))

    return result
