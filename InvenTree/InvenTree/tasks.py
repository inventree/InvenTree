# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import json
import requests
import logging

from datetime import datetime, timedelta

from django.core.exceptions import AppRegistryNotReady
from django.db.utils import OperationalError, ProgrammingError


logger = logging.getLogger("inventree")


def schedule_task(taskname, **kwargs):
    """
    Create a scheduled task.
    If the task has already been scheduled, ignore!
    """

    # If unspecified, repeat indefinitely
    repeats = kwargs.pop('repeats', -1)
    kwargs['repeats'] = repeats

    try:
        from django_q.models import Schedule
    except (AppRegistryNotReady):
        logger.warning("Could not start background tasks - App registry not ready")
        return

    try:
        # If this task is already scheduled, don't schedule it again
        # Instead, update the scheduling parameters
        if Schedule.objects.filter(func=taskname).exists():
            logger.info(f"Scheduled task '{taskname}' already exists - updating!")

            Schedule.objects.filter(func=taskname).update(**kwargs)
        else:
            logger.info(f"Creating scheduled task '{taskname}'")

            Schedule.objects.create(
                name=taskname,
                func=taskname,
                **kwargs
            )
    except (OperationalError, ProgrammingError):
        # Required if the DB is not ready yet
        pass


def offload_task(taskname, *args, **kwargs):
    """
    Create an AsyncTask.
    This is different to a 'scheduled' task,
    in that it only runs once!
    """

    try:
        from django_q.tasks import AsyncTask
    except (AppRegistryNotReady):
        logger.warning("Could not offload task - app registry not ready")
        return

    task = AsyncTask(taskname, *args, **kwargs)

    task.run()


def heartbeat():
    """
    Simple task which runs at 5 minute intervals,
    so we can determine that the background worker
    is actually running.

    (There is probably a less "hacky" way of achieving this)?
    """

    try:
        from django_q.models import Success
        logger.warning("Could not perform heartbeat task - App registry not ready")
    except AppRegistryNotReady:
        return

    threshold = datetime.now() - timedelta(minutes=30)

    # Delete heartbeat results more than half an hour old,
    # otherwise they just create extra noise
    heartbeats = Success.objects.filter(
        func='InvenTree.tasks.heartbeat',
        started__lte=threshold
    )

    heartbeats.delete()


def delete_successful_tasks():
    """
    Delete successful task logs
    which are more than a month old.
    """

    try:
        from django_q.models import Success
    except AppRegistryNotReady:
        logger.warning("Could not perform 'delete_successful_tasks' - App registry not ready")
        return

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
        # Apps not yet loaded!
        return

    response = requests.get('https://api.github.com/repos/inventree/inventree/releases/latest')

    if not response.status_code == 200:
        raise ValueError(f'Unexpected status code from GitHub API: {response.status_code}')

    data = json.loads(response.text)

    tag = data.get('tag_name', None)

    if not tag:
        raise ValueError("'tag_name' missing from GitHub response")

    match = re.match(r"^.*(\d+)\.(\d+)\.(\d+).*$", tag)

    if not len(match.groups()) == 3:
        logger.warning(f"Version '{tag}' did not match expected pattern")
        return

    latest_version = [int(x) for x in match.groups()]

    if not len(latest_version) == 3:
        raise ValueError(f"Version '{tag}' is not correct format")

    logger.info(f"Latest InvenTree version: '{tag}'")

    # Save the version to the database
    common.models.InvenTreeSetting.set_setting(
        'INVENTREE_LATEST_VERSION',
        tag,
        None
    )


def send_email(subject, body, recipients, from_email=None):
    """
    Send an email with the specified subject and body,
    to the specified recipients list.
    """

    if type(recipients) == str:
        recipients = [recipients]

    offload_task(
        'django.core.mail.send_mail',
        subject, body,
        from_email,
        recipients,
    )
