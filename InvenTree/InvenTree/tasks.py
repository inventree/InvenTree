# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import requests
import logging

from datetime import timedelta

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

        
def delete_successful_tasks():
    """
    Delete successful task logs
    which are more than a week old.
    """

    pass

def check_for_updates():
    """
    Check if there is an update for InvenTree
    """

    response = requests.get('https://api.github.com/repos/inventree/inventree/releases/latest')

    if not response.status_code == 200:
        logger.warning(f'Unexpected status code from GitHub API: {response.status_code}')
        return

    data = json.loads(response.text)

    print("Response:")
    print(data)
    # TODO 

    return data


def test(x):
    print(f"Running at task! {x}")