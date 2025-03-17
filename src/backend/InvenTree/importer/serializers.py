"""API serializers for the importer app."""

import json

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

import importer.models
import importer.registry
from InvenTree.serializers import (
    InvenTreeAttachmentSerializerField,
    InvenTreeModelSerializer,
    UserSerializer,
)


class DataImportColumnMapSerializer(InvenTreeModelSerializer):
    """Serializer for the DataImportColumnMap model."""

    class Meta:
        """Meta class options for the serializer."""

        model = importer.models.DataImportColumnMap
        fields = ['pk', 'session', 'column', 'field', 'label', 'description']
        read_only_fields = ['field', 'session']

    label = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)


class DataImportSessionSerializer(InvenTreeModelSerializer):
    """Serializer for the DataImportSession model."""

    class Meta:
        """Meta class options for the serializer."""

        model = importer.models.DataImportSession
        fields = [
            'pk',
            'timestamp',
            'data_file',
            'model_type',
            'available_fields',
            'status',
            'user',
            'user_detail',
            'columns',
            'column_mappings',
            'field_defaults',
            'field_overrides',
            'field_filters',
            'row_count',
            'completed_row_count',
        ]
        read_only_fields = ['pk', 'user', 'status', 'columns']

    def __init__(self, *args, **kwargs):
        """Override the constructor for the DataImportSession serializer."""
        super().__init__(*args, **kwargs)

        self.fields['model_type'].choices = importer.registry.supported_model_options()

    data_file = InvenTreeAttachmentSerializerField()

    model_type = serializers.ChoiceField(
        required=True,
        allow_blank=False,
        choices=importer.registry.supported_model_options(),
    )

    available_fields = serializers.JSONField(read_only=True)

    row_count = serializers.IntegerField(read_only=True)
    completed_row_count = serializers.IntegerField(read_only=True)

    column_mappings = DataImportColumnMapSerializer(many=True, read_only=True)

    user_detail = UserSerializer(source='user', read_only=True, many=False)

    def validate_field_defaults(self, defaults):
        """De-stringify the field defaults."""
        if defaults is None:
            return None

        if type(defaults) is not dict:
            try:
                defaults = json.loads(str(defaults))
            except:
                raise ValidationError(_('Invalid field defaults'))

        return defaults

    def validate_field_overrides(self, overrides):
        """De-stringify the field overrides."""
        if overrides is None:
            return None

        if type(overrides) is not dict:
            try:
                overrides = json.loads(str(overrides))
            except:
                raise ValidationError(_('Invalid field overrides'))

        return overrides

    def validate_field_filters(self, filters):
        """De-stringify the field filters."""
        if filters is None:
            return None

        if type(filters) is not dict:
            try:
                filters = json.loads(str(filters))
            except:
                raise ValidationError(_('Invalid field filters'))

        return filters

    def create(self, validated_data):
        """Override create method for this serializer.

        Attach user information based on provided session data.
        """
        session = super().create(validated_data)

        request = self.context.get('request', None)

        if request:
            session.user = request.user
            session.save()

        return session


class DataImportRowSerializer(InvenTreeModelSerializer):
    """Serializer for the DataImportRow model."""

    class Meta:
        """Meta class options for the serializer."""

        model = importer.models.DataImportRow
        fields = [
            'pk',
            'session',
            'row_index',
            'row_data',
            'data',
            'errors',
            'valid',
            'complete',
        ]

        read_only_fields = [
            'pk',
            'session',
            'row_index',
            'row_data',
            'errors',
            'valid',
            'complete',
        ]


class DataImportAcceptRowSerializer(serializers.Serializer):
    """Serializer for accepting rows of data."""

    class Meta:
        """Serializer meta options."""

        fields = ['rows']

    rows = serializers.PrimaryKeyRelatedField(
        queryset=importer.models.DataImportRow.objects.all(),
        many=True,
        required=True,
        label=_('Rows'),
        help_text=_('List of row IDs to accept'),
    )

    def validate_rows(self, rows):
        """Ensure that the provided rows are valid.

        - Row must point to the same import session
        - Row must contain valid data
        - Row must not have already been completed
        """
        session = self.context.get('session', None)

        if not rows or len(rows) == 0:
            raise ValidationError(_('No rows provided'))

        for row in rows:
            if row.session != session:
                raise ValidationError(_('Row does not belong to this session'))

            if not row.valid:
                raise ValidationError(_('Row contains invalid data'))

            if row.complete:
                raise ValidationError(_('Row has already been completed'))

        return rows

    def save(self):
        """Complete the provided rows."""
        rows = self.validated_data['rows']

        request = self.context.get('request', None)

        for row in rows:
            row.validate(commit=True, request=request)

        if session := self.context.get('session', None):
            session.check_complete()

        return rows
