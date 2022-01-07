"""
Functions for triggering and responding to server side events
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.conf import settings
from django.db import transaction

from common.models import InvenTreeSetting

from InvenTree.tasks import offload_task

from plugin.registry import plugin_registry


logger = logging.getLogger('inventree')


def trigger_event(event, *args, **kwargs):
    """
    Trigger an event with optional arguments.

    This event will be stored in the database,
    and the worker will respond to it later on.
    """

    logger.debug(f"Event triggered: '{event}'")

    offload_task(
        'plugin.events.process_event',
        event,
        *args,
        **kwargs,
    )


def process_event(event, *args, **kwargs):
    """
    Respond to a triggered event.

    This function is run by the background worker process.

    This function may queue multiple functions to be handled by the background worker.
    """

    logger.info(f"Processing event '{event}'")

    # Determine if there are any plugins which are interested in responding
    if settings.PLUGIN_TESTING or InvenTreeSetting.get_setting('ENABLE_PLUGINS_EVENTS'):

        # Run atomically, to ensure that either *all* tasks are registered, or *none*
        with transaction.atomic():
            for slug, callbacks in plugin_registry.mixins_events.items():
                # slug = plugin slug
                # callbacks = list of (event, function) tuples

                for _event, _func in callbacks:
                    if _event == event:

                        logger.info(f"Running task '{_func}' for plugin '{slug}'")

                        offload_task(
                            _func,
                            *args,
                            **kwargs
                        )
