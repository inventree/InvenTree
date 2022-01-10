"""
Functions for triggering and responding to server side events
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver

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
        'plugin.events.register_event',
        event,
        *args,
        **kwargs
    )


def register_event(event, *args, **kwargs):
    """
    Register the event with any interested plugins.

    Note: This function is processed by the background worker,
    as it performs multiple database access operations.
    """

    logger.debug(f"Registering triggered event: '{event}'")

    # Determine if there are any plugins which are interested in responding
    if settings.PLUGIN_TESTING or InvenTreeSetting.get_setting('ENABLE_PLUGINS_EVENTS'):

        with transaction.atomic():

            for slug, plugin in plugin_registry.plugins.items():

                if plugin.mixin_enabled('events'):

                    config = plugin.plugin_config()

                    if config and config.active:

                        logger.debug(f"Registering callback for plugin '{slug}'")

                        # Offload a separate task for each plugin
                        offload_task(
                            'plugin.events.process_event',
                            slug,
                            event,
                            *args,
                            **kwargs
                        )


def process_event(plugin_slug, event, *args, **kwargs):
    """
    Respond to a triggered event.

    This function is run by the background worker process.

    This function may queue multiple functions to be handled by the background worker.
    """

    logger.info(f"Plugin '{plugin_slug}' is processing triggered event '{event}'")

    plugin = plugin_registry.plugins[plugin_slug]

    plugin.process_event(event, *args, **kwargs)


"""
Register some default event triggers on model signals
"""

@receiver(post_save)
def after_save(sender, instance, created, **kwargs):
    """
    Trigger an event whenever a database entry is saved
    """

    table = sender.objects.model._meta.db_table

    if table.startswith('django_q'):
        # Ignore django_q tables, to avoid recursion
        return

    if created:
        trigger_event(
            'instance.created',
            id=instance.id,
            model=sender.__name__,
            table=table,
        )
    else:
        trigger_event(
            'instance.saved',
            id=instance.id,
            model=sender.__name__,
            table=table,
        )


@receiver(post_delete)
def after_delete(sender, instance, **kwargs):
    """
    Trigger an event whenever a database entry is deleted
    """

    table = sender.objects.model._meta.db_table

    if table.startswith('django_q'):
        # Ignore django_q tables, to avoid recursion
        return

    trigger_event(
        'instance.deleted',
        model=sender.__name__,
        table=table,
    )
