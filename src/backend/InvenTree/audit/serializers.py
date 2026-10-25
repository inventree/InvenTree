"""API serializers for the audit app."""

from typing import Any, Optional

from django.core.exceptions import (
    FieldDoesNotExist,
    ObjectDoesNotExist,
    ValidationError,
)
from django.db import models
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

import InvenTree.serializers
from audit.models import MASKED_VALUE, AuditLogEntry
from InvenTree.serializers import OptionalField
from users.serializers import UserSerializer


class AuditChangeDetailSerializer(serializers.Serializer):
    """Describes a single field change within an audit log entry."""

    field = serializers.CharField(label=_('Field'))
    label = serializers.CharField(label=_('Label'))
    type = serializers.ChoiceField(
        choices=['value', 'fk', 'm2m'], label=_('Change Type')
    )
    old = serializers.JSONField(allow_null=True, required=False)
    new = serializers.JSONField(allow_null=True, required=False)
    old_display = serializers.CharField(allow_null=True, required=False)
    new_display = serializers.CharField(allow_null=True, required=False)
    model_type = serializers.CharField(
        allow_null=True, required=False, help_text=_('Related model (for FK fields)')
    )
    operation = serializers.CharField(
        allow_null=True, required=False, help_text=_('M2M operation (add / delete)')
    )
    objects = serializers.ListField(
        child=serializers.CharField(), allow_null=True, required=False
    )
    numeric = serializers.BooleanField(
        required=False, help_text=_('The field holds a numeric value')
    )


def is_numeric_field(field) -> bool:
    """Return True if the model field holds a plain numeric value.

    Fields with choices are excluded (their values are displayed via the choice label).
    Note: decimal values are recorded as strings (e.g. '10.00000').
    """
    if field is None or getattr(field, 'flatchoices', None):
        return False

    return isinstance(
        field, (models.IntegerField, models.DecimalField, models.FloatField)
    )


class AuditLogEntrySerializer(
    InvenTree.serializers.FilterableSerializerMixin,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Serializer for the AuditLogEntry model (read-only)."""

    # Fields which are only exposed to staff users
    STAFF_ONLY_FIELDS = ['remote_addr', 'remote_port']

    class Meta:
        """Metaclass options."""

        model = AuditLogEntry
        fields = [
            'pk',
            'timestamp',
            'action',
            'action_label',
            'actor',
            'actor_detail',
            'actor_username',
            'event_type',
            'event_label',
            'notes',
            'deltas',
            'model_type',
            'model_label',
            'object_pk',
            'object_repr',
            'parent_model_type',
            'parent_object_pk',
            'changes',
            'changes_detail',
            'cid',
            'additional_data',
            'remote_addr',
            'remote_port',
        ]
        read_only_fields = fields

    action_label = serializers.CharField(
        source='get_action_display', read_only=True, label=_('Action')
    )

    model_type = serializers.CharField(read_only=True, label=_('Model Type'))

    model_label = serializers.SerializerMethodField(label=_('Model Label'))

    def get_model_label(self, entry: AuditLogEntry) -> str:
        """Return the human readable name of the audited model."""
        if model := entry.content_type.model_class():
            return capfirst(str(model._meta.verbose_name))

        return entry.model_type

    parent_model_type = serializers.CharField(
        read_only=True, allow_null=True, label=_('Parent Model Type')
    )

    event_label = serializers.CharField(
        read_only=True, allow_null=True, label=_('Event')
    )

    deltas = serializers.SerializerMethodField(label=_('Deltas'))

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_deltas(self, entry: AuditLogEntry) -> Optional[dict]:
        """Return the deltas recorded against a named event.

        References to objects which the user cannot view are redacted.
        """
        deltas = (entry.additional_data or {}).get('deltas')

        if not isinstance(deltas, dict):
            return None

        return {key: self.redact_reference(value) for key, value in deltas.items()}

    def redact_reference(self, value):
        """Redact a reference to a model instance, if the user cannot view the model."""
        from django.apps import apps

        if not (isinstance(value, dict) and 'model_type' in value and 'pk' in value):
            return value

        try:
            model = apps.get_model(value['model_type'])
        except (LookupError, ValueError):
            model = None

        if self.can_view_model(model):
            return value

        return {**value, 'pk': None, 'str': None}

    changes = serializers.SerializerMethodField(label=_('Changes'))

    changes_detail = OptionalField(
        serializer_class=serializers.SerializerMethodField,
        serializer_kwargs={'read_only': True, 'label': _('Change Details')},
        default_include=False,
    )

    def get_request_user(self):
        """Return the requesting user (if any)."""
        request = self.context.get('request')
        return getattr(request, 'user', None)

    def can_view_model(self, model) -> bool:
        """Return True if the requesting user may view the given model (cached)."""
        from audit.permissions import user_can_view_audit_model

        if model is None:
            return False

        cache = self.__dict__.setdefault('_audit_perm_cache', {})

        if model not in cache:
            cache[model] = user_can_view_audit_model(self.get_request_user(), model)

        return cache[model]

    def get_entry_fields(self, entry: AuditLogEntry) -> dict:
        """Return a mapping of field name -> model field for the audited model."""
        model = entry.content_type.model_class()
        fields = {}

        # The audited model may no longer exist (e.g. an uninstalled plugin)
        if model is None:
            return fields

        for name in entry.changes_dict or {}:
            try:
                fields[name] = model._meta.get_field(name)
            except FieldDoesNotExist:
                continue

        return fields

    @extend_schema_field(serializers.JSONField())
    def get_changes(self, entry: AuditLogEntry) -> dict:
        """Return the raw changes recorded against this entry.

        The string representation of related objects in M2M changes is
        removed where the user cannot view the related model.
        """
        changes = dict(entry.changes_dict or {})
        fields = self.get_entry_fields(entry)

        for name, value in changes.items():
            if isinstance(value, dict) and value.get('type') == 'm2m':
                field = fields.get(name)
                related = getattr(field, 'related_model', None)

                if not self.can_view_model(related):
                    changes[name] = {**value, 'objects': None}

        return changes

    def get_related_display(self, model, value) -> Optional[str]:
        """Return the string representation of a related object (if it can be viewed)."""
        if value in (None, '', 'None', MASKED_VALUE) or not self.can_view_model(model):
            return None

        cache = self.__dict__.setdefault('_audit_fk_cache', {})
        key = (model, str(value))

        if key not in cache:
            try:
                pk = model._meta.pk.to_python(value)
                cache[key] = str(model._base_manager.get(pk=pk))
            except ObjectDoesNotExist:
                cache[key] = _('Deleted')
            except (ValidationError, ValueError, TypeError):
                cache[key] = None

        return cache[key]

    @extend_schema_field(AuditChangeDetailSerializer(many=True))
    def get_changes_detail(self, entry: AuditLogEntry) -> list[dict[str, Any]]:
        """Return a list of per-field changes, with display values.

        - Field labels are resolved from the model (if it still exists)
        - Choice values are translated to their labels
        - Foreign key values are resolved to the related object, *only* if the
          requesting user has permission to view the related model
        """
        fields = self.get_entry_fields(entry)
        rows = []

        for name, value in self.get_changes(entry).items():
            field = fields.get(name)

            # The primary key is recorded on creation, but is not useful to display
            if getattr(field, 'primary_key', False):
                continue

            label = capfirst(str(getattr(field, 'verbose_name', name)))

            row = {
                'field': name,
                'label': label,
                'type': 'value',
                'old': None,
                'new': None,
                'old_display': None,
                'new_display': None,
                'model_type': None,
                'operation': None,
                'objects': None,
                'numeric': is_numeric_field(field),
            }

            if isinstance(value, dict) and value.get('type') == 'm2m':
                row['type'] = 'm2m'
                row['operation'] = value.get('operation')
                row['objects'] = value.get('objects')
                rows.append(row)
                continue

            if isinstance(value, (list, tuple)) and len(value) == 2:
                row['old'], row['new'] = value
            else:
                row['new'] = value

            related = getattr(field, 'related_model', None)

            if (
                field is not None
                and related
                and (field.many_to_one or field.one_to_one)
            ):
                row['type'] = 'fk'
                row['model_type'] = (
                    f'{related._meta.app_label}.{related._meta.model_name}'
                )
                row['old_display'] = self.get_related_display(related, row['old'])
                row['new_display'] = self.get_related_display(related, row['new'])

            elif field is not None and getattr(field, 'flatchoices', None):
                choices = dict(field.flatchoices)

                for key in ['old', 'new']:
                    if row[key] in choices:
                        row[f'{key}_display'] = str(choices[row[key]])

            rows.append(row)

        # Order by the model field definition order (unknown fields last)
        model = entry.content_type.model_class()
        order = (
            {f.name: idx for idx, f in enumerate(model._meta.get_fields())}
            if model
            else {}
        )

        rows.sort(key=lambda row: order.get(row['field'], len(order)))

        return rows

    actor_detail = OptionalField(
        serializer_class=UserSerializer,
        serializer_kwargs={'source': 'actor', 'read_only': True, 'allow_null': True},
        default_include=True,
        prefetch_fields=['actor'],
    )

    def to_representation(self, instance):
        """Remove staff-only fields for non-staff users."""
        data = super().to_representation(instance)

        user = self.get_request_user()

        if not (user and user.is_staff):
            for field in self.STAFF_ONLY_FIELDS:
                data.pop(field, None)

        # Event deltas are provided (with redaction) via the 'deltas' field
        if isinstance(data.get('additional_data'), dict):
            additional_data = {
                key: value
                for key, value in data['additional_data'].items()
                if key != 'deltas'
            }
            data['additional_data'] = additional_data or None

        # Only expose the parent reference if the user may view the parent model
        if parent_ct := instance.parent_content_type:
            if not self.can_view_model(parent_ct.model_class()):
                data['parent_model_type'] = None
                data['parent_object_pk'] = None

        return data
