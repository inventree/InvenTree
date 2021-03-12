# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import json
import requests
import logging

from datetime import datetime, timedelta
from django.core.exceptions import AppRegistryNotReady


logger = logging.getLogger(__name__)


def schedule_task(taskname, **kwargs):
    """
    Create a scheduled task.
    If the task has already been scheduled, ignore!
    """

    try:
        from django_q.models import Schedule
    except (AppRegistryNotReady):
        logger.warning("Could not start background tasks - App registry not ready")
        return

    if Schedule.objects.filter(func=taskname).exists():
        logger.info(f"Scheduled task '{taskname}' already exists. (Skipping)")
    else:
        logger.info(f"Creating scheduled task '{taskname}'")

        Schedule.objects.create(
            func=taskname,
            **kwargs
        )


def heartbeat():
    """
    Simple task which runs at 5 minute intervals,
    so we can determine that the background worker
    is actually running.

    (There is probably a less "hacky" way of achieving this)
    """
    pass


def delete_successful_tasks():
    """
    Delete successful task logs
    which are more than a month old.
    """

    threshold = datetime.now() - timedelta(days=30)

    results = Success.objects.filter(
        started__lte=threshold
    )

    results.delete()


def check_for_updates():
    """
    Check if there is an update for InvenTree
    """

    try:
        import common.models
    except AppRegistryNotReady:
        return

    response = requests.get('https://api.github.com/repos/inventree/inventree/releases/latest')

    if not response.status_code == 200:
        logger.warning(f'Unexpected status code from GitHub API: {response.status_code}')
        return

    data = json.loads(response.text)

    tag = data.get('tag_name', None)

    if not tag:
        logger.warning("'tag_name' missing from GitHub response")
        return

    match = re.match(r"^.*(\d+)\.(\d+)\.(\d+).*$", tag)

    if not len(match.groups()) == 3:
        logger.warning(f"Version '{tag}' did not match expected pattern")
        return

    try:
        latest_version = [int(x) for x in match.groups()]
    except (ValueError):
        logger.warning(f"Version '{tag}' not integer format")
        return

    if not len(latest_version) == 3:
        logger.warning(f"Version '{tag}' is not correct format")
        return

    logger.info(f"Latest InvenTree version: '{tag}'")

    # Save the version to the database
    common.models.InvenTreeSetting.set_setting(
        'INVENTREE_LATEST_VERSION',
        tag,
        None
    )
