# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import requests
import logging

from datetime import timedelta


logger = logging.getLogger(__name__)


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

    # TODO 


def test(x):
    print(f"Running at task! {x}")