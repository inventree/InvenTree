"""
Provides system status functionality checks.
"""
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging

from django.utils.translation import ugettext as _

from django_q.monitor import Stat

logger = logging.getLogger(__name__)


def is_q_cluster_running(**kwargs):
    """
    Return True if at least one cluster worker is running
    """

    clusters = Stat.get_all()

    for cluster in clusters:
        print("Cluster:", cluster)

    return len(clusters) > 0


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
