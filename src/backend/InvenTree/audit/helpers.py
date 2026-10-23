"""Helper functions for recording audit entries for bulk database operations.

QuerySet.update() (and bulk_create / bulk_update) bypass model signals,
so changes made this way are not recorded by django-auditlog.
Code which modifies audited models in bulk should use these helpers instead.
"""

import contextlib

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import connection, transaction
from django.db.models.signals import pre_save

from auditlog.context import auditlog_disabled
from auditlog.registry import auditlog


def is_audited(model) -> bool:
    """Return True if changes to the given model are currently being audited."""
    try:
        disabled = auditlog_disabled.get()
    except LookupError:
        disabled = False

    return not disabled and auditlog.contains(model)


@contextlib.contextmanager
def write_batched():
    """Write all audit entries created within this context with a single bulk insert.

    Avoids one INSERT query per modified row for the bulk helpers below.
    Must be used within a transaction, so that the entries are written atomically with the changes.

    Note: post_log receivers are passed the (unsaved) log entry.
    """
    from audit.context import audit_batch
    from audit.models import AuditLogEntry

    with audit_batch() as entries:
        yield

        if entries:
            # Upstream applies context data (e.g. remote_addr) via a pre_save receiver,
            # which bulk_create() does not trigger
            for entry in entries:
                pre_save.send(
                    sender=AuditLogEntry,
                    instance=entry,
                    raw=False,
                    using=AuditLogEntry.objects.db,
                    update_fields=None,
                )

            AuditLogEntry.objects.bulk_create(entries)


def copy_related_cache(source, target) -> None:
    """Copy cached related objects from one instance of a model to another.

    Avoids re-fetching related objects (e.g. for the audit entry string representation)
    for rows which have been re-read from the database. Only relations whose
    foreign key value is unchanged between the two instances are copied.
    """
    for name, related in source._state.fields_cache.items():
        try:
            field = source._meta.get_field(name)
        except FieldDoesNotExist:
            continue

        attname = getattr(field, 'attname', None)

        if (
            attname
            and (field.many_to_one or field.one_to_one)
            and getattr(source, attname, None) == getattr(target, attname, None)
        ):
            target._state.fields_cache.setdefault(name, related)


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

        with write_batched():
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


def audited_bulk_update(model, objs: list, fields: list[str], **kwargs) -> int:
    """Perform Model.objects.bulk_update(), recording an audit entry for each modified row.

    As with audited_update(), the old and new values are read from the database,
    so the recorded changes reflect what was actually written (including F() expressions).

    Arguments:
        model: The model class
        objs: The (saved) model instances to update
        fields: The fields to update
        kwargs: Additional arguments passed through to bulk_update() (e.g. batch_size)

    Returns:
        int: The number of rows updated (as per bulk_update())
    """
    from auditlog.receivers import _create_log_entry

    from audit.models import AuditLogEntry

    if not is_audited(model):
        return model.objects.bulk_update(objs, fields, **kwargs)

    manager = model._base_manager
    pks = [obj.pk for obj in objs]

    with transaction.atomic():
        if connection.features.has_select_for_update:
            old_rows = manager.select_for_update().in_bulk(pks)
        else:
            old_rows = manager.in_bulk(pks)

        count = model.objects.bulk_update(objs, fields, **kwargs)

        new_rows = manager.in_bulk(pks)

        # Reuse any related objects already loaded by the caller
        for obj in objs:
            if new := new_rows.get(obj.pk):
                copy_related_cache(obj, new)

        with write_batched():
            for pk, old in old_rows.items():
                if new := new_rows.get(pk):
                    _create_log_entry(
                        action=AuditLogEntry.Action.UPDATE,
                        instance=new,
                        sender=model,
                        diff_old=old,
                        diff_new=new,
                        fields_to_check=list(fields),
                        use_json_for_changes=settings.AUDITLOG_STORE_JSON_CHANGES,
                    )

    return count


def audited_bulk_create(model, objs: list) -> list:
    """Bulk create model instances, recording a CREATE audit entry for each new row.

    Uses InvenTree.helpers_db.bulk_create_and_fetch() to resolve the created rows,
    so that entries are recorded on every database backend - including those which do
    not return primary keys from bulk_create() (e.g. MySQL).

    Primary keys are populated on the provided objects (as per bulk_create()).

    Arguments:
        model: The model class (must provide a 'metadata' field)
        objs: The (unsaved) model instances to create

    Returns:
        list: The created objects, as fetched from the database (in insertion order)
    """
    from auditlog.receivers import _create_log_entry

    from audit.models import AuditLogEntry
    from InvenTree.helpers_db import bulk_create_and_fetch

    # Required by bulk_create_and_fetch() - checked for all models (not only audited ones),
    # so that an unsupported model is caught in development rather than at runtime
    try:
        model._meta.get_field('metadata')
    except FieldDoesNotExist:
        raise TypeError(
            f"audited_bulk_create() requires a 'metadata' field: {model._meta.label}"
        )

    if not objs:
        return []

    with transaction.atomic():
        created = list(bulk_create_and_fetch(model, objs))

        if len(created) != len(objs):  # pragma: no cover
            raise ValueError(
                f'Expected {len(objs)} {model._meta.label} objects, fetched {len(created)}'
            )

        # Back-populate primary keys onto the provided objects
        for obj, instance in zip(objs, created, strict=True):
            obj.pk = instance.pk
            obj._state.adding = False
            obj._state.db = instance._state.db

        if is_audited(model):
            with write_batched():
                for instance in created:
                    _create_log_entry(
                        action=AuditLogEntry.Action.CREATE,
                        instance=instance,
                        sender=model,
                        diff_old=None,
                        diff_new=instance,
                        use_json_for_changes=settings.AUDITLOG_STORE_JSON_CHANGES,
                    )

    return created
