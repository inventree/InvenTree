"""Serializers for the exporter app."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

import exporter.models
import InvenTree.helpers
import InvenTree.serializers
from plugin import PluginMixinEnum, registry


class DataExportOptionsSerializer(serializers.Serializer):
    """Serializer class for defining a data export session."""

    class Meta:
        """Metaclass options for this serializer."""

        fields = ['export_format', 'export_plugin']

    def __init__(self, *args, **kwargs):
        """Construct the DataExportOptionsSerializer.

        - The exact nature of the available fields depends on which plugin is selected.
        - The selected plugin may 'extend' the fields available in the serializer.
        """
        # Reset fields to a known state
        self.Meta.fields = ['export_format', 'export_plugin']

        # Generate a list of plugins to choose from
        # If a model type is provided, use this to filter the list of plugins
        model_class = kwargs.pop('model_class', None)
        request = kwargs.pop('request', None)

        # Is a plugin serializer provided?
        if plugin := kwargs.pop('plugin', None):
            if hasattr(plugin, 'get_export_options_serializer'):
                plugin_serializer = plugin.get_export_options_serializer()

                if plugin_serializer:
                    for key, field in plugin_serializer.fields.items():
                        # Note: Custom fields *must* start with 'export_' prefix
                        if key.startswith('export_') and key not in self.Meta.fields:
                            self.Meta.fields.append(key)
                            setattr(self, key, field)

        plugin_options = []

        for plugin in registry.with_mixin(PluginMixinEnum.EXPORTER):
            if plugin.supports_export(model_class, request.user):
                plugin_options.append((plugin.slug, plugin.name))

        self.fields['export_plugin'].choices = plugin_options

        super().__init__(*args, **kwargs)

    export_format = serializers.ChoiceField(
        choices=InvenTree.helpers.GetExportOptions(),
        default='csv',
        label=_('Export Format'),
        help_text=_('Select export file format'),
    )

    # Select plugin for export - the options will be dynamically generated later on
    export_plugin = serializers.ChoiceField(
        choices=[],
        default='inventree-exporter',
        label=_('Export Plugin'),
        help_text=_('Select export plugin'),
    )


class DataExportOutputSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer class for a data export output object."""

    class Meta:
        """Metaclass options for this serializer."""

        model = exporter.models.ExportOutput
        fields = ['pk', 'created', 'user', 'plugin', 'complete', 'progress', 'output']

    output = InvenTree.serializers.InvenTreeAttachmentSerializerField()
