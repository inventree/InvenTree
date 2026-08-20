"""Functions for triggering and responding to server side events."""

import contextvars
from collections import defaultdict
from contextlib import contextmanager

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver

import structlog
from opentelemetry import trace

import InvenTree.exceptions
from common.settings import get_global_setting
from InvenTree.ready import canAppAccessDatabase, isImportingData
from InvenTree.tasks import bulk_offload_task, offload_task
from plugin import PluginMixinEnum
from plugin.registry import registry

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger('inventree')

# Active event batch for the current context (see batch_events()), if any
_event_batch: contextvars.ContextVar = contextvars.ContextVar(
    'event_batch', default=None
)


class EventBatch:
    """Collects trigger_event() calls made within a batch_events() scope.

    Entries are grouped by event name, so that each distinct event triggered
    within the batch is flushed via its own bulk_trigger_event() call.
    """

    def __init__(self):
        """Initialize an empty batch."""
        self.entries: dict[str, list] = defaultdict(list)

    def add(self, event: str, *args, **kwargs) -> None:
        """Record a single trigger_event() call against this batch."""
        self.entries[event].append((args, kwargs))

    def flush(self) -> None:
        """Fire a bulk_trigger_event() call for each event name collected so far."""
        entries, self.entries = self.entries, defaultdict(list)

        for event, event_entries in entries.items():
            bulk_trigger_event(event, event_entries)


@contextmanager
def batch_events():
    """Batch trigger_event() calls made within this scope into bulk_trigger_event() calls.

    Any trigger_event() call made (directly, or indirectly via a nested function call)
    while this context is active is queued instead of immediately offloaded. The queued
    events are flushed - grouped by event name, one bulk_trigger_event() call per name -
    when the current database transaction commits (or immediately, if no transaction is
    active). If the transaction is instead rolled back, the queued events are discarded,
    rather than being fired for a write that never happened.

    Nesting is not supported: a nested batch_events() call reuses the outer batch, and
    only the outermost call schedules a flush.

    This does not change the behavior of code that triggers events *outside* of this
    context - trigger_event() still fires immediately in that case. This allows existing
    single-item entrypoints (e.g. StockItem.stocktake()) to be reused unmodified by both
    single-item and bulk callers: bulk callers simply wrap their loop in batch_events().

    Yields:
        EventBatch: The current event batch, which can be used to add events directly.

    """
    if _event_batch.get() is not None:
        # Already inside a batch - extend it, rather than creating a nested one
        yield _event_batch.get()
        return

    batch = EventBatch()
    token = _event_batch.set(batch)

    try:
        yield batch
    finally:
        _event_batch.reset(token)
        transaction.on_commit(batch.flush)


@tracer.start_as_current_span('trigger_event')
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

    if (batch := _event_batch.get()) is not None:
        # A batch_events() context is active - queue this event rather than firing it now
        batch.add(event, *args, **kwargs)
        return

    logger.debug("Event triggered: '%s'", event)

    force_async = kwargs.pop('force_async', True)

    # If we are running in testing mode, we can enable or disable async processing
    if settings.PLUGIN_TESTING_EVENTS:
        force_async = settings.PLUGIN_TESTING_EVENTS_ASYNC

    kwargs['force_async'] = force_async

    offload_task(register_event, event, *args, group='plugin', **kwargs)


@tracer.start_as_current_span('bulk_trigger_event')
def bulk_trigger_event(event: str, entries: list) -> None:
    """Trigger the same event multiple times, in a single bulk database write.

    Equivalent to calling trigger_event(event, *args, **kwargs) once per (args, kwargs)
    pair in 'entries', but queues all of the resulting background tasks via a single
    bulk_offload_task() call, rather than one INSERT per event.

    Arguments:
        event: The event to trigger
        entries: List of (args, kwargs) tuples, one per event instance to register

    These events will be stored in the database, and the worker will respond to them later on.
    """
    if not entries:
        return

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
        logger.debug("Ignoring bulk triggered event '%s' - database not ready", event)
        return

    logger.debug("Bulk event triggered: '%s' (%s entries)", event, len(entries))

    force_async = True

    # If we are running in testing mode, we can enable or disable async processing
    if settings.PLUGIN_TESTING_EVENTS:
        force_async = settings.PLUGIN_TESTING_EVENTS_ASYNC

    task_entries = []

    for args, kwargs in entries:
        kwargs = dict(kwargs)
        # 'force_async' is a bulk_offload_task() control flag, not event data - it is
        # resolved once for the whole batch above, so strip any per-entry override
        kwargs.pop('force_async', None)
        task_entries.append(((event, *args), kwargs))

    bulk_offload_task(
        register_event, task_entries, group='plugin', force_async=force_async
    )


@tracer.start_as_current_span('register_event')
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
            for plugin in registry.with_mixin(PluginMixinEnum.EVENTS, active=True):
                # Let the plugin decide if it wants to process this event
                if not plugin.wants_process_event(event):
                    continue

                logger.debug("Registering callback for plugin '%s'", plugin.slug)

                # This task *must* be processed by the background worker,
                # unless we are running CI tests
                if 'force_async' not in kwargs and not settings.PLUGIN_TESTING_EVENTS:
                    kwargs['force_async'] = True

                # Offload a separate task for each plugin
                offload_task(
                    process_event, plugin.slug, event, *args, group='plugin', **kwargs
                )


@tracer.start_as_current_span('process_event')
def process_event(plugin_slug, event, *args, **kwargs):
    """Respond to a triggered event.

    This function is run by the background worker process.
    This function may queue multiple functions to be handled by the background worker.
    """
    plugin = registry.get_plugin(plugin_slug, active=True)

    if plugin is None:  # pragma: no cover
        logger.error("Could not find matching active plugin for '%s'", plugin_slug)
        return

    logger.debug("Plugin '%s' is processing triggered event '%s'", plugin_slug, event)

    try:
        plugin.process_event(event, *args, **kwargs)
    except Exception as e:
        # Log the exception to the database
        InvenTree.exceptions.log_error('process_event', plugin=plugin_slug)
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
