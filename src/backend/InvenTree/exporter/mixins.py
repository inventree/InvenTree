"""Mixin classes for the exporter app."""

from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import structlog
import tablib
from rest_framework import serializers
from taggit.serializers import TagListSerializerField

import InvenTree.exceptions
from exporter.serializers import DataExportOptionsSerializer
from InvenTree.helpers import DownloadFile, str2bool
from plugin import PluginMixinEnum, registry

logger = structlog.get_logger('inventree')


class DataExportSerializerMixin:
    """Mixin class for adding data export functionality to a DRF serializer.

    Provides generic functionality to take the output of a serializer and export it to a file.

    Attributes:
        export_only_fields: List of field names which are only used during data export
        export_exclude_fields: List of field names which are excluded during data export
        export_child_fields: List of child fields which are exported (using dot notation)
    """

    export_only_fields = []
    export_exclude_fields = []
    export_child_fields = []

    def get_export_only_fields(self, **kwargs) -> list:
        """Return the list of field names which are only used during data export."""
        return self.export_only_fields

    def get_export_exclude_fields(self, **kwargs) -> list:
        """Return the list of field names which are excluded during data export."""
        return self.export_exclude_fields

    def __init__(self, *args, **kwargs):
        """Initialise the DataExportSerializerMixin.

        Determine if the serializer is being used for data export,
        and if so, adjust the serializer fields accordingly.
        """
        exporting = kwargs.pop('exporting', False)

        super().__init__(*args, **kwargs)

        # Cache the request object
        self.request = self.context.get('request')

        if exporting:
            # Exclude fields which are not required for data export
            for field in self.get_export_exclude_fields(**kwargs):
                self.fields.pop(field, None)
        else:
            # Exclude fields which are only used for data export
            for field in self.get_export_only_fields(**kwargs):
                self.fields.pop(field, None)

    def get_exportable_fields(self) -> dict:
        """Return a dict of fields which can be exported against this serializer instance.

        Note: Any fields which should be excluded from export have already been removed

        Returns:
            dict: A dictionary of field names and field objects
        """
        fields = {}

        if meta := getattr(self, 'Meta', None):
            write_only_fields = getattr(meta, 'write_only_fields', [])
        else:
            write_only_fields = []

        for name, field in self.fields.items():
            # Skip write-only fields
            if getattr(field, 'write_only', False) or name in write_only_fields:
                continue

            # Skip tags fields
            # TODO: Implement tag field export support
            if issubclass(field.__class__, TagListSerializerField):
                continue

            # Top-level serializer fields can be exported with dot notation
            if issubclass(field.__class__, serializers.Serializer):
                fields.update(self.get_child_fields(name, field))
                continue

            fields[name] = field

        return fields

    def get_child_fields(self, field_name: str, field) -> dict:
        """Return a dictionary of child fields for a given field.

        Only child fields which match the 'export_child_fields' list will be returned.
        """
        child_fields = {}

        if sub_fields := getattr(field, 'fields', None):
            for sub_name, sub_field in sub_fields.items():
                name = f'{field_name}.{sub_name}'

                if name in self.export_child_fields:
                    sub_field.parent_field = field
                    child_fields[name] = sub_field

        return child_fields

    @classmethod
    def arrange_export_headers(cls, headers: list) -> list:
        """Optional method to arrange the export headers.

        By default, the headers are returned in the order they are provided.
        """
        return headers

    def get_nested_value(self, row: dict, key: str) -> any:
        """Get a nested value from a dictionary.

        This method allows for dot notation to access nested fields.

        Arguments:
            row: The dictionary to extract the value from
            key: The key to extract

        Returns:
            any: The extracted value
        """
        keys = key.split('.')

        value = row

        for key in keys:
            if not value:
                break

            if not key:
                continue

            value = value.get(key, None)

        return value

    def generate_headers(self) -> OrderedDict:
        """Generate a list of default headers for the exported data.

        Returns an ordered dict of field names and their corresponding human-readable labels.

        e.g.

        {
            'id': 'ID',
            'name': 'Name',
            ...
        }

        """
        fields = self.get_exportable_fields()
        field_names = self.arrange_export_headers(list(fields.keys()))

        headers = OrderedDict()

        for field_name in field_names:
            field = fields[field_name]

            label = getattr(field, 'label', field_name)

            if parent := getattr(field, 'parent_field', None):
                label = f'{parent.label}.{label}'

            headers[field_name] = label

        return headers

    def export_to_file(self, data, headers: OrderedDict, file_format):
        """Export the queryset to a file in the specified format.

        Arguments:
            queryset: The queryset to export
            data: The serialized dataset to export
            headers: The headers to use for the exported data {field: label}
            file_format: The file format to export to

        Returns:
            File object containing the exported data
        """
        field_names = list(headers.keys())
        field_headers = list(headers.values())

        # Create a new dataset with the provided header labels
        dataset = tablib.Dataset(headers=field_headers)

        for row in data:
            dataset.append([self.get_nested_value(row, f) for f in field_names])

        return dataset.export(file_format)


class DataExportViewMixin:
    """An API view mixin for directly exporting selected data.

    To perform a data export against an API endpoint which inherits from this mixin,
    perform a POST request with 'export=True'.

    This will run validation against the DataExportOptionsSerializer.

    Once the export options have been validated, a new DataExportOutput object will be created,
    and this will be returned to the client (including a download link to the exported file).
    """

    def is_exporting(self) -> bool:
        """Determine if the view is currently exporting data."""
        if request := getattr(self, 'request', None):
            return str2bool(
                request.data.get('export') or request.query_params.get('export')
            )

        return False

    def get_plugin(self, plugin_slug=None):
        """Return the plugin instance associated with the export request.

        Arguments:
            plugin_slug: The slug of the plugin to use for exporting the data (optional)
        """
        if not plugin_slug:
            if request := getattr(self, 'request', None):
                plugin_slug = request.data.get('plugin') or request.query_params.get(
                    'plugin'
                )

        if plugin_slug:
            return registry.get_plugin(
                plugin_slug, active=True, with_mixin=PluginMixinEnum.EXPORTER
            )

        return None

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for the view.

        - Only applies for OPTIONS or POST requests
        - OPTIONS requests to determine plugin serializer options
        - POST request to perform the data export
        - If the view is exporting data, return the DataExportOptionsSerializer.
        - Otherwise, return the default serializer.
        """
        exporting = kwargs.pop('exporting', None)

        if exporting is None:
            exporting = (
                self.request.method.lower() in ['options', 'post']
                and self.is_exporting()
            )

        if exporting:
            kwargs['plugin'] = self.get_plugin()
            kwargs['request'] = self.request

            # Get the base model associated with this view
            try:
                serializer_class = self.get_serializer_class()
                kwargs['model_class'] = serializer_class.Meta.model
            except AttributeError:
                kwargs['model_class'] = None

            return DataExportOptionsSerializer(*args, **kwargs)
        else:
            return super().get_serializer(*args, **kwargs)

    def export_data(self, export_plugin, export_format, export_context):
        """Export the data in the specified format.

        Arguments:
            export_plugin: The plugin instance to use for exporting the data
            export_format: The file format to export the data in
            export_context: Additional context data to pass to the plugin

        - By default, uses the provided serializer to generate the data, and return it as a file download.
        - If a plugin is specified, the plugin can be used to augment or replace the export functionality.
        """
        # Get the base serializer class for the view
        serializer_class = self.get_serializer_class()

        if not issubclass(serializer_class, DataExportSerializerMixin):
            raise ValidationError(
                'Serializer class must inherit from DataExportSerialierMixin'
            )

        export_error = _('Error occurred during data export')

        context = self.get_serializer_context()

        # Perform initial filtering of the queryset, based on the query parameters
        queryset = self.filter_queryset(self.get_queryset())

        # Perform additional filtering, as per the provided plugin
        try:
            queryset = export_plugin.filter_queryset(queryset)
        except Exception:
            InvenTree.exceptions.log_error(
                f'plugins.{export_plugin.slug}.filter_queryset'
            )
            raise ValidationError(export_error)

        data = None
        serializer = serializer_class(context=context, exporting=True)
        serializer.initial_data = queryset

        # Construct 'defualt' headers (note: may be overridden by plugin)
        headers = serializer.generate_headers()

        # Generate a filename for the exported data (implemented by the plugin)
        try:
            filename = export_plugin.generate_filename(
                serializer_class.Meta.model, export_format
            )
        except Exception:
            InvenTree.exceptions.log_error(
                f'plugins.{export_plugin.slug}.generate_filename'
            )
            raise ValidationError(export_error)

        # The provided plugin is responsible for exporting the data
        # The returned data *must* be a list of dict objects
        try:
            data = export_plugin.export_data(
                queryset, serializer_class=serializer_class, headers=headers
            )

        except Exception:
            InvenTree.exceptions.log_error(f'plugins.{export_plugin.slug}.export_data')
            raise ValidationError(export_error)

        if not isinstance(data, list):
            raise ValidationError(
                _('Data export plugin returned incorrect data format')
            )

        # Augment / update the headers (if required)
        if hasattr(export_plugin, 'update_headers'):
            try:
                headers = export_plugin.update_headers(headers)
            except Exception:
                InvenTree.exceptions.log_error(
                    f'plugins.{export_plugin.slug}.update_headers'
                )
                raise ValidationError(export_error)

        # Now, export the data to file
        try:
            datafile = serializer.export_to_file(data, headers, export_format)
        except Exception:
            InvenTree.exceptions.log_error('export_to_file')
            raise ValidationError(_('Error occurred during data export'))

        # Finally, return a file download object
        return DownloadFile(datafile, filename=filename)

    def post(self, request, *args, **kwargs):
        """Override the POST method to determine export options."""
        # If we are not exporting data, return the default response
        if self.is_exporting():
            # Determine if the export options are valid
            serializer = self.get_serializer(exporting=True, data=request.data)
            serializer.is_valid(raise_exception=True)

            # Serializer is valid - export the data

            export_context = serializer.validated_data

            plugin_slug = export_context.pop('export_plugin', None)
            export_plugin = self.get_plugin(plugin_slug)
            export_format = export_context.pop('export_format', 'csv')

            # Add in extra context data for the plugin
            export_context['request'] = request
            export_context['user'] = request.user

            return self.export_data(
                export_plugin=export_plugin,
                export_format=export_format,
                export_context=export_context,
            )

        return super().post(request, *args, **kwargs)
