"""Serializers for the exporter app."""

from rest_framework import serializers

import exporter.models


class DataExportOptionsSerializer(serializers.Serializer):
    """Serializer class for defining a data export session."""

    class Meta:
        """Metaclass options for this serializer."""

        fields = ['export_format', 'export_plugin']

    export_format = serializers.ChoiceField(
        choices=[('csv', 'CSV'), ('xlsx', 'Excel'), ('pdf', 'PDF'), ('json', 'JSON')],
        default='csv',
        help_text='Export file format',
    )

    export_plugin = serializers.CharField(
        max_length=100, help_text='Export plugin name'
    )


class DataExportOutputSerializer(serializers.Serializer):
    """Serializer class for a data export output object."""

    class Meta:
        """Metaclass options for this serializer."""

        model = exporter.models.ExportOutput
        fields = ['pk', 'created', 'user', 'plugin', 'complete', 'progress', 'output']
