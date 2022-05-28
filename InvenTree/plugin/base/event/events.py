"""Functions for triggering and responding to server side events"""

import logging

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver

from InvenTree.ready import canAppAccessDatabase, isImportingData
from InvenTree.tasks import offload_task
from plugin.registry import registry

logger = logging.getLogger('inventree')


def trigger_event(event, *args, **kwargs):
    """Trigger an event with optional arguments.

    This event will be stored in the database,
    and the worker will respond to it later on.
    """
    if not settings.PLUGINS_ENABLED:
        # Do nothing if plugins are not enabled
        return  # pragma: no cover

    # Make sure the database can be accessed and is not beeing tested rn
    if not canAppAccessDatabase() and not settings.PLUGIN_TESTING_EVENTS:
        logger.debug(f"Ignoring triggered event '{event}' - database not ready")
        return

    logger.debug(f"Event triggered: '{event}'")

    offload_task(
        register_event,
        event,
        *args,
        **kwargs
    )


def register_event(event, *args, **kwargs):
    """Register the event with any interested plugins.

    Note: This function is processed by the background worker,
    as it performs multiple database access operations.
    """
    from common.models import InvenTreeSetting

    logger.debug(f"Registering triggered event: '{event}'")

    # Determine if there are any plugins which are interested in responding
    if settings.PLUGIN_TESTING or InvenTreeSetting.get_setting('ENABLE_PLUGINS_EVENTS'):

        with transaction.atomic():

            for slug, plugin in registry.plugins.items():

                if plugin.mixin_enabled('events'):

                    config = plugin.plugin_config()

                    if config and config.active:

                        logger.debug(f"Registering callback for plugin '{slug}'")

                        # Offload a separate task for each plugin
                        offload_task(
                            process_event,
                            slug,
                            event,
                            *args,
                            **kwargs
                        )


def process_event(plugin_slug, event, *args, **kwargs):
    """Respond to a triggered event.

    This function is run by the background worker process.
    This function may queue multiple functions to be handled by the background worker.
    """
    logger.info(f"Plugin '{plugin_slug}' is processing triggered event '{event}'")

    plugin = registry.plugins.get(plugin_slug, None)

    if plugin is None:  # pragma: no cover
        logger.error(f"Could not find matching plugin for '{plugin_slug}'")
        return

    plugin.process_event(event, *args, **kwargs)


def allow_table_event(table_name):
    """Determine if an automatic event should be fired for a given table.

    We *do not* want events to be fired for some tables!
    """
    if isImportingData():
        # Prevent table events during the data import process
        return False  # pragma: no cover

    table_name = table_name.lower().strip()

    # Ignore any tables which start with these prefixes
    ignore_prefixes = [
        'account_',
        'auth_',
        'authtoken_',
        'django_',
        'error_',
        'exchange_',
        'otp_',
        'plugin_',
        'socialaccount_',
        'user_',
        'users_',
    ]

    if any([table_name.startswith(prefix) for prefix in ignore_prefixes]):
        return False

    ignore_tables = [
        'common_notificationentry',
        'common_webhookendpoint',
        'common_webhookmessage',
    ]

    if table_name in ignore_tables:
        return False

    return True


@receiver(post_save)
def after_save(sender, instance, created, **kwargs):
    """Trigger an event whenever a database entry is saved"""
    table = sender.objects.model._meta.db_table

    instance_id = getattr(instance, 'id', None)

    if instance_id is None:
        return

    if not allow_table_event(table):
        return

    if created:
        trigger_event(
            f'{table}.created',
            id=instance.id,
            model=sender.__name__,
        )
    else:
        trigger_event(
            f'{table}.saved',
            id=instance.id,
            model=sender.__name__,
        )


@receiver(post_delete)
def after_delete(sender, instance, **kwargs):
    """Trigger an event whenever a database entry is deleted"""
    table = sender.objects.model._meta.db_table

    if not allow_table_event(table):
        return

    trigger_event(
        f'{table}.deleted',
        model=sender.__name__,
    )
