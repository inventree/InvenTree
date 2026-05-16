"""Serializers for the exporter app."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

import InvenTree.exceptions
import InvenTree.helpers
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
        serializer_class = kwargs.pop('serializer_class', None)
        model_class = kwargs.pop('model_class', None)
        view_class = kwargs.pop('view_class', None)

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
            try:
                supports_export = plugin.supports_export(
                    model_class,
                    user=request.user if request else None,
                    serializer_class=serializer_class,
                    view_class=view_class,
                )
            except Exception:
                InvenTree.exceptions.log_error('supports_export', plugin=plugin.slug)
                supports_export = False

            if supports_export:
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
