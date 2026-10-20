"""API serializers for the audit app."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

import InvenTree.serializers
from audit.models import AuditLogEntry
from InvenTree.serializers import OptionalField
from users.serializers import UserSerializer


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
            'model_type',
            'object_pk',
            'object_repr',
            'parent_model_type',
            'parent_object_pk',
            'changes',
            'changes_display',
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

    parent_model_type = serializers.CharField(
        read_only=True, allow_null=True, label=_('Parent Model Type')
    )

    changes = serializers.JSONField(
        source='changes_dict', read_only=True, label=_('Changes')
    )

    changes_display = OptionalField(
        serializer_class=serializers.JSONField,
        serializer_kwargs={
            'source': 'changes_display_dict',
            'read_only': True,
            'label': _('Changes (display)'),
        },
        default_include=False,
    )

    actor_detail = OptionalField(
        serializer_class=UserSerializer,
        serializer_kwargs={'source': 'actor', 'read_only': True, 'allow_null': True},
        default_include=True,
        prefetch_fields=['actor'],
    )

    def to_representation(self, instance):
        """Remove staff-only fields for non-staff users."""
        data = super().to_representation(instance)

        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if not (user and user.is_staff):
            for field in self.STAFF_ONLY_FIELDS:
                data.pop(field, None)

        return data
