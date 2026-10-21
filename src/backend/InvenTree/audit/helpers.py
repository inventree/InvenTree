"""Helper functions for recording audit entries for bulk database operations.

QuerySet.update() (and bulk_create / bulk_update) bypass model signals,
so changes made this way are not recorded by django-auditlog.
Code which modifies audited models in bulk should use these helpers instead.
"""

from django.conf import settings
from django.db import connection, transaction

from auditlog.context import auditlog_disabled
from auditlog.registry import auditlog


def is_audited(model) -> bool:
    """Return True if changes to the given model are currently being audited."""
    try:
        disabled = auditlog_disabled.get()
    except LookupError:
        disabled = False

    return not disabled and auditlog.contains(model)


def audited_update(queryset, **values) -> int:
    """Perform QuerySet.update(), recording an audit entry for each modified row.

    Supports any value accepted by QuerySet.update() (including F() expressions),
    as the new values are re-read from the database after the update.

    Arguments:
        queryset: The queryset to update
        values: The field values to update

    Returns:
        int: The number of rows updated (as per QuerySet.update())
    """
    # Imported here to keep the dependency on this (private) upstream function in one place.
    # It provides the same pre_log / diff / log_create / post_log path as the model signals.
    # Pinned via requirements: django-auditlog>=3.4.1,<4
    from auditlog.receivers import _create_log_entry

    from audit.models import AuditLogEntry

    model = queryset.model

    if not is_audited(model):
        return queryset.update(**values)

    manager = model._base_manager

    with transaction.atomic():
        if connection.features.has_select_for_update:
            old_rows = list(queryset.select_for_update())
        else:
            old_rows = list(queryset)

        if not old_rows:
            return 0

        pks = [row.pk for row in old_rows]

        # Update by PK - the original queryset may filter on the fields being updated
        count = manager.filter(pk__in=pks).update(**values)

        new_rows = manager.in_bulk(pks)

        for old in old_rows:
            if new := new_rows.get(old.pk):
                _create_log_entry(
                    action=AuditLogEntry.Action.UPDATE,
                    instance=new,
                    sender=model,
                    diff_old=old,
                    diff_new=new,
                    fields_to_check=list(values.keys()),
                    use_json_for_changes=settings.AUDITLOG_STORE_JSON_CHANGES,
                )

    return count
