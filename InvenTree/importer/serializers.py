"""API serializers for the importer app."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

import importer.models
from InvenTree.serializers import InvenTreeModelSerializer


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
            'status',
            'user',
            'columns',
            'field_defaults',
            'field_mapping',
            'row_count',
            'completed_row_count',
        ]
        read_only_fields = ['pk', 'user', 'status', 'columns']

    row_count = serializers.IntegerField(read_only=True)
    completed_row_count = serializers.IntegerField(read_only=True)

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
