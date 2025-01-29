"""Functions for triggering and responding to server side events."""

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver

import structlog

import InvenTree.exceptions
from common.settings import get_global_setting
from InvenTree.ready import canAppAccessDatabase, isImportingData
from InvenTree.tasks import offload_task
from plugin.registry import registry

logger = structlog.get_logger('inventree')


def trigger_event(event: str, *args, **kwargs) -> None:
    """Trigger an event with optional arguments.

    Arguments:
        event: The event to trigger
        *args: Additional arguments to pass to the event handler
        **kwargs: Additional keyword arguments to pass to the event handler

    This event will be stored in the database, and the worker will respond to it later on.
    """
    if not get_global_setting('ENABLE_PLUGINS_EVENTS', False):
        # Do nothing if plugin events are not enabled
        return

    # Ensure event name is stringified
    event = str(event).strip()

    # Make sure the database can be accessed and is not being tested rn
    if (
        not canAppAccessDatabase(allow_shell=True)
        and not settings.PLUGIN_TESTING_EVENTS
    ):
        logger.debug("Ignoring triggered event '%s' - database not ready", event)
        return

    logger.debug("Event triggered: '%s'", event)

    force_async = kwargs.pop('force_async', True)

    # If we are running in testing mode, we can enable or disable async processing
    if settings.PLUGIN_TESTING_EVENTS:
        force_async = settings.PLUGIN_TESTING_EVENTS_ASYNC

    kwargs['force_async'] = force_async

    offload_task(register_event, event, *args, group='plugin', **kwargs)


def register_event(event, *args, **kwargs):
    """Register the event with any interested plugins.

    Note: This function is processed by the background worker,
    as it performs multiple database access operations.
    """
    logger.debug("Registering triggered event: '%s'", event)

    # Determine if there are any plugins which are interested in responding
    if settings.PLUGIN_TESTING or get_global_setting('ENABLE_PLUGINS_EVENTS'):
        # Check if the plugin registry needs to be reloaded
        registry.check_reload()

        with transaction.atomic():
            for slug, plugin in registry.plugins.items():
                if not plugin.mixin_enabled('events'):
                    continue

                # Only allow event registering for 'active' plugins
                if not plugin.is_active():
                    continue

                # Let the plugin decide if it wants to process this event
                if not plugin.wants_process_event(event):
                    continue

                logger.debug("Registering callback for plugin '%s'", slug)

                # This task *must* be processed by the background worker,
                # unless we are running CI tests
                if 'force_async' not in kwargs and not settings.PLUGIN_TESTING_EVENTS:
                    kwargs['force_async'] = True

                # Offload a separate task for each plugin
                offload_task(
                    process_event, slug, event, *args, group='plugin', **kwargs
                )


def process_event(plugin_slug, event, *args, **kwargs):
    """Respond to a triggered event.

    This function is run by the background worker process.
    This function may queue multiple functions to be handled by the background worker.
    """
    plugin = registry.get_plugin(plugin_slug)

    if plugin is None:  # pragma: no cover
        logger.error("Could not find matching plugin for '%s'", plugin_slug)
        return

    logger.debug("Plugin '%s' is processing triggered event '%s'", plugin_slug, event)

    try:
        plugin.process_event(event, *args, **kwargs)
    except Exception as e:
        # Log the exception to the database
        InvenTree.exceptions.log_error(f'plugins.{plugin_slug}.process_event')
        # Re-throw the exception so that the background worker tries again
        raise e


def allow_table_event(table_name):
    """Determine if an automatic event should be fired for a given table.

    We *do not* want events to be fired for some tables!
    """
    # Prevent table events during the data import process
    if isImportingData():
        return False  # pragma: no cover

    # Prevent table events when in testing mode (saves a lot of time)
    if settings.TESTING and not settings.TESTING_TABLE_EVENTS:
        return False

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
        'importer_',
    ]

    if any(table_name.startswith(prefix) for prefix in ignore_prefixes):
        return False

    ignore_tables = [
        'common_notificationentry',
        'common_notificationmessage',
        'common_webhookendpoint',
        'common_webhookmessage',
        'part_partpricing',
        'part_partstocktake',
        'part_partstocktakereport',
    ]

    return table_name not in ignore_tables


@receiver(post_save)
def after_save(sender, instance, created, **kwargs):
    """Trigger an event whenever a database entry is saved."""
    table = sender.objects.model._meta.db_table

    instance_id = getattr(instance, 'id', None)

    if instance_id is None:
        return

    if not allow_table_event(table):
        return

    if created:
        trigger_event(f'{table}.created', id=instance.id, model=sender.__name__)
    else:
        trigger_event(f'{table}.saved', id=instance.id, model=sender.__name__)


@receiver(post_delete)
def after_delete(sender, instance, **kwargs):
    """Trigger an event whenever a database entry is deleted."""
    table = sender.objects.model._meta.db_table

    if not allow_table_event(table):
        return

    instance_id = None

    if instance:
        instance_id = getattr(instance, 'id', None)

    trigger_event(f'{table}.deleted', model=sender.__name__, id=instance_id)
