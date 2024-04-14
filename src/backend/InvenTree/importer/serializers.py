"""API serializers for the importer app."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

import importer.models
import importer.registry
from InvenTree.serializers import (
    InvenTreeAttachmentSerializerField,
    InvenTreeModelSerializer,
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
            'columns',
            'column_mappings',
            'field_defaults',
            'row_count',
            'completed_row_count',
        ]
        read_only_fields = ['pk', 'user', 'status', 'columns']

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
            'data',
            'errors',
            'valid',
            'complete',
        ]
