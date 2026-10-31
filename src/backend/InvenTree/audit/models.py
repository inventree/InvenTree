"""Database models for the audit app."""

import os
from typing import Optional

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _

from auditlog.models import AbstractLogEntry, LogEntryManager

import audit.context

MASKED_VALUE = '***'

# Maximum length of the notes associated with an audit entry
NOTES_MAX_LENGTH = 512


def get_audit_parent_reference(instance):
    """Return a (ContentType, pk) reference to the audit "parent" of an instance (or None)."""
    if callable(func := getattr(instance, 'get_audit_parent_reference', None)):
        return func()

    # Fallback for models which provide get_audit_parent() only
    if callable(func := getattr(instance, 'get_audit_parent', None)):
        if parent := func():
            return ContentType.objects.get_for_model(parent), str(parent.pk)

    return None


# Attribute used to defer an audit entry until the instance has been saved
DEFERRED_LOG_ATTR = '_audit_deferred_log'


def expression_fields(instance, changes: dict) -> list[str]:
    """Return the changed fields whose (unsaved) value is a query expression (e.g. F('x') + 1).

    The value written by such an expression is only known once the instance has been saved.
    """
    fields = []

    for name in changes:
        try:
            field = type(instance)._meta.get_field(name)
        except FieldDoesNotExist:
            continue

        # Read the raw attribute value - avoids any related object lookups
        value = instance.__dict__.get(getattr(field, 'attname', name))

        if hasattr(value, 'resolve_expression'):
            fields.append(name)

    return fields


def file_field_basenames(model, changes: dict) -> dict:
    """Reduce recorded file field values to the filename only (not the full storage path)."""
    for name, value in changes.items():
        try:
            field = model._meta.get_field(name)
        except FieldDoesNotExist:
            continue

        if isinstance(field, models.FileField) and isinstance(value, (list, tuple)):
            changes[name] = [
                os.path.basename(v) if isinstance(v, str) and v else v for v in value
            ]

    return changes


def resolve_lazy_strings(changes: dict) -> dict:
    """Convert lazy translation strings to plain strings, so that the changes are JSON serializable.

    Upstream only performs this conversion when AUDITLOG_STORE_JSON_CHANGES is disabled.
    """
    for name, value in changes.items():
        if isinstance(value, (list, tuple)):
            changes[name] = [str(v) if isinstance(v, Promise) else v for v in value]

    return changes


def drop_orphan_currency_changes(instance, changes: dict) -> dict:
    """Remove changes to money currency fields whose amount is not set (and has not changed).

    django-money stores the currency of a MoneyField 'x' in a separate field 'x_currency',
    which has a default value (e.g. 'USD') even when the amount is empty.
    Without this, creating an object records e.g. {'price_currency': [None, 'USD']}.
    """
    from djmoney.models.fields import MoneyField

    result = {}

    for field, value in changes.items():
        if field.endswith('_currency'):
            amount = field[: -len('_currency')]

            try:
                amount_field = type(instance)._meta.get_field(amount)
            except FieldDoesNotExist:
                amount_field = None

            # Only applies to the currency field of a MoneyField (e.g. not 'order_currency')
            if (
                isinstance(amount_field, MoneyField)
                and amount not in changes
                and getattr(instance, amount, None) is None
            ):
                continue

        result[field] = value

    return result


def is_unchanged_value(value) -> bool:
    """Return True if a recorded [old, new] change pair does not represent a real change.

    None and '' are treated as equivalent, as nullable string fields (e.g. Part.IPN)
    may hold either value for "empty" - e.g. a NULL value saved from a form as ''.
    """
    if not (isinstance(value, (list, tuple)) and len(value) == 2):
        return False

    old, new = (None if v == '' else v for v in value)

    return old == new


def is_concrete_field(model, field_name: str) -> bool:
    """Return True if field_name is a concrete field on the model (or is unknown)."""
    try:
        field = model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return True

    return getattr(field, 'concrete', False)


def mask_changes(changes):
    """Replace every recorded value in the provided changes dict."""
    if not changes:
        return changes

    masked = {}

    for field, value in changes.items():
        if isinstance(value, dict) and value.get('type') == 'm2m':
            masked[field] = {
                **value,
                'objects': [MASKED_VALUE for _obj in value.get('objects', [])],
            }
        else:
            masked[field] = [MASKED_VALUE, MASKED_VALUE]

    return masked


class AuditLogEntryManager(LogEntryManager):
    """Manager for the AuditLogEntry model.

    Extends the upstream manager to attach InvenTree specific context to each entry:
    - Parent object reference
    - Actor (resolved lazily from the current request)
    - Source (for changes made outside of a request)
    - Row-level masking of sensitive values
    """

    def get_audit_kwargs(self, instance, kwargs: dict) -> dict:
        """Update the provided LogEntry kwargs with InvenTree specific data."""
        if reference := get_audit_parent_reference(instance):
            parent_ct, parent_pk = reference
            kwargs.setdefault('parent_content_type', parent_ct)
            kwargs.setdefault('parent_object_pk', parent_pk)

        # A pending named event for this instance (see audit.helpers.audit_event)
        event = audit.context.consume_event(instance)

        # The actor is (in order of preference) provided explicitly, by the event, or by the request
        if 'actor' not in kwargs and (
            actor := (event and event.actor) or audit.context.get_request_actor()
        ):
            kwargs['actor'] = actor
            kwargs['actor_email'] = getattr(actor, 'email', None)

        # Record the username, so that the actor is still identified if the user is deleted
        if (actor := kwargs.get('actor')) and not kwargs.get('actor_username'):
            kwargs['actor_username'] = getattr(actor, 'username', None)

        if source := audit.context.get_source():
            get_additional_data = getattr(instance, 'get_additional_data', None)

            additional_data = kwargs.get('additional_data')

            if additional_data is None and callable(get_additional_data):
                additional_data = get_additional_data()

            kwargs['additional_data'] = {**(additional_data or {}), 'source': source}

        # Attach the pending named event
        if event:
            kwargs['event_type'] = event.event_type
            kwargs['notes'] = event.notes or None

            # Deltas which are already recorded as field changes are not duplicated
            changes = kwargs.get('changes')
            deltas = {
                key: value
                for key, value in (event.deltas or {}).items()
                if not (isinstance(changes, dict) and key in changes)
            }

            if deltas:
                kwargs['additional_data'] = {
                    **(kwargs.get('additional_data') or {}),
                    'deltas': deltas,
                }

        is_masked = getattr(instance, 'is_audit_masked', None)

        if callable(is_masked) and is_masked():
            # Mask at write time - sensitive values must never reach the log table
            kwargs['changes'] = mask_changes(kwargs.get('changes'))
            kwargs['serialized_data'] = None
            kwargs['notes'] = None

            if additional_data := kwargs.get('additional_data'):
                additional_data.pop('deltas', None)

        return kwargs

    def log_create(self, instance, force_log: bool = False, **kwargs):
        """Create a new log entry for the provided instance.

        For updates, fields whose recorded old and new values are identical (or both empty,
        i.e. None or '') are dropped. These occur when the in-memory value differs from the
        database value only in type (e.g. an empty FieldFile vs. an empty string, or a NULL
        value saved from a form as ''), and would otherwise add noise to every save.

        Updates which assign a query expression (e.g. F('completed') + 1) are deferred until
        after the save, so that the value actually written can be recorded
        (see audit.signals.resolve_deferred_log).
        """
        # Internal flag: this entry has been deferred, and the expression values resolved
        resolved = kwargs.pop('_audit_resolved', False)

        changes = kwargs.get('changes')

        if isinstance(changes, dict):
            # Upstream includes reverse relations (e.g. 'company.contacts') in create / delete diffs,
            # recording the string representation of the related manager - discard these
            changes = {
                field: value
                for field, value in changes.items()
                if is_concrete_field(type(instance), field)
            }

            # A money currency field (e.g. 'price_currency') is meaningless without an amount
            changes = drop_orphan_currency_changes(instance, changes)

            if not changes and not force_log:
                return None

            if kwargs.get('action') == AuditLogEntry.Action.UPDATE:
                if not resolved and (fields := expression_fields(instance, changes)):
                    instance.__dict__[DEFERRED_LOG_ATTR] = {
                        'force_log': force_log,
                        'kwargs': {**kwargs, 'changes': changes},
                        'fields': fields,
                    }
                    return None

                changes = {
                    field: value
                    for field, value in changes.items()
                    if not is_unchanged_value(value)
                }

                if not changes and not force_log:
                    return None

            kwargs['changes'] = file_field_basenames(
                type(instance), resolve_lazy_strings(changes)
            )

        kwargs = self.get_audit_kwargs(instance, kwargs)
        return super().log_create(instance, force_log=force_log, **kwargs)

    def create(self, **kwargs):
        """Create a new log entry, or add it to the current batch (see audit.helpers.write_batched)."""
        if (batch := audit.context.get_batch()) is not None:
            entry = self.model(**kwargs)
            batch.append(entry)
            return entry

        return super().create(**kwargs)

    def log_m2m_changes(
        self, changed_queryset, instance, operation, field_name, **kwargs
    ):
        """Create a new log entry for a many-to-many change."""
        is_masked = getattr(instance, 'is_audit_masked', None)

        if callable(is_masked) and is_masked() and changed_queryset:
            # Upstream builds the 'changes' dict from str(obj) for each object,
            # so substitute placeholders before anything is written
            changed_queryset = [MASKED_VALUE] * len(changed_queryset)

        kwargs = self.get_audit_kwargs(instance, kwargs)

        return super().log_m2m_changes(
            changed_queryset, instance, operation, field_name, **kwargs
        )


class AuditLogEntry(AbstractLogEntry):
    """A single audit log entry, recording a change to a model instance.

    Extends the upstream LogEntry with an (optional) reference to a "parent" object,
    so that the history of a parent (e.g. a PurchaseOrder) can include changes
    made to its children (e.g. line items) - even after the child has been deleted.

    Entries are immutable via the API.
    """

    class Meta(AbstractLogEntry.Meta):
        """Metaclass options for the AuditLogEntry model."""

        verbose_name = _('Audit Log Entry')
        verbose_name_plural = _('Audit Log Entries')

        indexes = [
            models.Index(
                fields=['content_type', 'object_pk', '-timestamp'],
                name='audit_object_idx',
            ),
            models.Index(
                fields=['parent_content_type', 'parent_object_pk', '-timestamp'],
                name='audit_parent_idx',
            ),
        ]

    objects = AuditLogEntryManager()

    # Note: SET_NULL (rather than CASCADE) so that removing a stale content type
    # (e.g. an uninstalled plugin) does not delete the history of child objects
    parent_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('Parent Content Type'),
    )

    parent_object_pk = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_('Parent Object PK')
    )

    # Snapshot of the actor's username (retained if the user is deleted)
    actor_username = models.CharField(
        max_length=150, null=True, blank=True, verbose_name=_('Actor Username')
    )

    # Named event type (see InvenTreeAuditMixin.AUDIT_EVENT_TYPES)
    event_type = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_('Event Type')
    )

    notes = models.CharField(
        max_length=NOTES_MAX_LENGTH,
        null=True,
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Notes associated with this entry'),
    )

    @property
    def event_label(self) -> Optional[str]:
        """Return the label for the event type of this entry (if any)."""
        from audit.registry import event_type_label

        if self.event_type is None:
            return None

        return event_type_label(self.content_type.model_class(), self.event_type)

    @property
    def model_type(self) -> str:
        """Return the 'app_label.model' string for the audited model."""
        return f'{self.content_type.app_label}.{self.content_type.model}'

    @property
    def parent_model_type(self):
        """Return the 'app_label.model' string for the parent model (if any)."""
        if ct := self.parent_content_type:
            return f'{ct.app_label}.{ct.model}'
        return None
