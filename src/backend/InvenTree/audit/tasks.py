"""Background tasks for the audit app."""

from datetime import timedelta

from django.db.models import Exists, OuterRef
from django.utils import timezone

import structlog
from opentelemetry import trace

from common.settings import get_global_setting
from InvenTree.tasks import ScheduledTask, scheduled_task

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger('inventree')

# Number of entries to delete per query
DELETE_BATCH_SIZE = 1000


@tracer.start_as_current_span('delete_old_audit_entries')
@scheduled_task(ScheduledTask.DAILY)
def delete_old_audit_entries():
    """Remove audit log entries older than the configured retention period.

    Entries are deleted in small batches, so that no single long-running
    transaction holds locks on the (potentially very large) audit table.

    If AUDIT_LOG_DELETE_KEEP_SUMMARY is enabled, the following entries are retained
    for each object (regardless of age), so that it is always known who created
    and who last modified an object:
    - The CREATE entry
    - The most recent entry (for a deleted object, this is the DELETE entry)
    """
    from audit.models import AuditLogEntry

    if not get_global_setting('AUDIT_LOG_DELETE_OLD_ENTRIES', False):
        return

    delete_n_days = int(get_global_setting('AUDIT_LOG_DELETE_DAYS', 365))

    threshold = timezone.now() - timedelta(days=delete_n_days)

    old_entries = AuditLogEntry.objects.filter(timestamp__lte=threshold)

    if get_global_setting('AUDIT_LOG_DELETE_KEEP_SUMMARY', True):
        # Only delete entries which have a newer entry for the same object
        newer_entries = AuditLogEntry.objects.filter(
            content_type=OuterRef('content_type'),
            object_pk=OuterRef('object_pk'),
            pk__gt=OuterRef('pk'),
        )

        old_entries = old_entries.exclude(action=AuditLogEntry.Action.CREATE).filter(
            Exists(newer_entries)
        )

    deleted = 0

    while batch := list(old_entries.values_list('pk', flat=True)[:DELETE_BATCH_SIZE]):
        n, _ = AuditLogEntry.objects.filter(pk__in=batch).delete()
        deleted += n

    if deleted:
        logger.info('Deleted old audit log entries', count=deleted, threshold=threshold)
