"""
Functions for triggering and responding to server side events
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from InvenTree.tasks import offload_task


logger = logging.getLogger('inventree')


def trigger_event(event, *args, **kwargs):
    """
    Trigger an even with optional arguments.

    This event will be stored in the database,
    and the worker will respond to it later on.
    """

    logger.debug(f"Event triggered: '{event}'")

    offload_task(
        'InvenTree.events.process_event',
        event,
        *args,
        **kwargs,
    )

def process_event(event, *args, **kwargs):
    """
    Respond to a triggered event.
    
    This function is run by the background worker process.
    """

    logger.info(f"Processing event '{event}'")

    # Determine if there are any plugins which are interested in responding
