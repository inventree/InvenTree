"""Mixin classes for the exporter app."""

from collections import OrderedDict
from typing import Any

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _

import structlog
import tablib
from rest_framework import serializers
from rest_framework.response import Response
from taggit.serializers import TagListSerializerField

import data_exporter.serializers
import data_exporter.tasks
import InvenTree.exceptions
from common.models import DataOutput
from InvenTree.helpers import str2bool
from InvenTree.tasks import offload_task
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
        self._exporting_data = exporting = kwargs.pop('exporting', False)

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

    def get_nested_value(self, row: dict, key: str) -> Any:
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
    perform a GET request with 'export=True'.

    This will run validation against the DataExportOptionsSerializer.

    Once the export options have been validated, a new DataOutput object will be created,
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
        PLUGIN_KEY = 'export_plugin'

        if not plugin_slug:
            if request := getattr(self, 'request', None):
                plugin_slug = request.data.get(PLUGIN_KEY) or request.query_params.get(
                    PLUGIN_KEY
                )

        if plugin_slug:
            return registry.get_plugin(
                plugin_slug, active=True, with_mixin=PluginMixinEnum.EXPORTER
            )

        return None

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for the view.

        - Only applies for OPTIONS or GET requests
        - OPTIONS requests to determine plugin serializer options
        - GET request to perform the data export
        - If the view is exporting data, return the DataExportOptionsSerializer.
        - Otherwise, return the default serializer.
        """
        exporting = kwargs.pop('exporting', None)

        if exporting is None:
            method = str(getattr(self.request, 'method', '')).lower()
            exporting = method in ['options', 'get'] and self.is_exporting()

        if exporting:
            # Override kwargs when initializing the DataExportOptionsSerializer
            export_kwargs = {
                'plugin': self.get_plugin(),
                'request': self.request,
                'data': kwargs.get('data'),
                'context': kwargs.get('context'),
            }

            # Get the base model associated with this view
            try:
                serializer_class = self.get_serializer_class()
                export_kwargs['serializer_class'] = serializer_class
                export_kwargs['model_class'] = serializer_class.Meta.model
                export_kwargs['view_class'] = self.__class__
            except AttributeError:
                # If the serializer class is not available, set to None
                export_kwargs['serializer_class'] = None
                export_kwargs['model_class'] = None
                export_kwargs['view_class'] = None

            return data_exporter.serializers.DataExportOptionsSerializer(
                *args, **export_kwargs
            )
        else:
            return super().get_serializer(*args, **kwargs)

    def export_data(
        self,
        export_plugin,
        export_format: str,
        export_context: dict,
        output: DataOutput,
    ):
        """Export the data in the specified format.

        Arguments:
            export_plugin: The plugin instance to use for exporting the data
            export_format: The file format to export the data in
            export_context: Additional context data to pass to the plugin
            output: The DataOutput object to write to

        - By default, uses the provided serializer to generate the data, and return it as a file download.
        - If a plugin is specified, the plugin can be used to augment or replace the export functionality.
        """
        # Get the base serializer class for the view
        serializer_class = self.get_serializer_class()

        if not issubclass(serializer_class, DataExportSerializerMixin):
            raise ValidationError(
                'Serializer class must inherit from DataExportSerializerMixin'
            )

        export_error = _('Error occurred during data export')

        context = self.get_serializer_context()

        # Perform initial filtering of the queryset, based on the query parameters
        queryset = self.filter_queryset(self.get_queryset())

        # Perform additional filtering, as per the provided plugin
        try:
            queryset = export_plugin.filter_queryset(queryset)
        except Exception:
            InvenTree.exceptions.log_error('filter_queryset', plugin=export_plugin.slug)
            raise ValidationError(export_error)

        # Update the output instance with the total number of items to export
        output.total = queryset.count()
        output.save()

        data = None
        serializer = serializer_class(context=context, exporting=True)
        serializer.initial_data = queryset

        # Construct 'default' headers (note: may be overridden by plugin)
        headers = serializer.generate_headers()

        # Generate a filename for the exported data (implemented by the plugin)
        try:
            filename = export_plugin.generate_filename(
                serializer_class.Meta.model, export_format
            )
        except Exception as e:
            InvenTree.exceptions.log_error(
                'generate_filename', plugin=export_plugin.slug
            )

            output.mark_failure(error=str(e))

            raise ValidationError(export_error)

        # The provided plugin is responsible for exporting the data
        # The returned data *must* be a list of dict objects
        try:
            data = export_plugin.export_data(
                queryset, serializer_class, headers, export_context, output
            )

        except Exception as e:
            InvenTree.exceptions.log_error('export_data', plugin=export_plugin.slug)

            # Log the error against the output object
            output.mark_failure(error=str(e))

            raise ValidationError(export_error)

        if not isinstance(data, list):
            raise ValidationError(
                _('Data export plugin returned incorrect data format')
            )

        # Augment / update the headers (if required)
        if hasattr(export_plugin, 'update_headers'):
            try:
                headers = export_plugin.update_headers(headers, export_context)
            except Exception as e:
                InvenTree.exceptions.log_error(
                    'update_headers', plugin=export_plugin.slug
                )

                output.mark_failure(error=str(e))

                raise ValidationError(export_error)

        # Now, export the data to file
        try:
            datafile = serializer.export_to_file(data, headers, export_format)
        except Exception as e:
            InvenTree.exceptions.log_error('export_to_file', plugin=export_plugin.slug)
            output.mark_failure(error=str(e))
            raise ValidationError(_('Error occurred during data export'))

        # Update the output object with the exported data
        output.mark_complete(output=ContentFile(datafile, filename))

    def get(self, request, *args, **kwargs):
        """Override the GET method to determine export options."""
        from common.serializers import DataOutputSerializer

        # If we are not exporting data, return the default response
        if self.is_exporting():
            # Determine if the export options are valid

            # Extract the export options from the provided query parameters
            export_options = {}

            for key in request.query_params:
                if key.startswith('export_'):
                    export_options[key] = request.query_params.get(key)

            # Construct the options serializer with the provided data
            serializer = self.get_serializer(exporting=True, data=export_options)

            serializer.is_valid(raise_exception=True)
            serializer_data = serializer.validated_data

            export_format = serializer_data.pop('export_format', 'csv')
            plugin_slug = serializer_data.pop('export_plugin', 'inventree-exporter')
            export_plugin = self.get_plugin(plugin_slug)

            export_context = {}

            # Also run the data against the plugin serializer
            if export_plugin:
                if hasattr(export_plugin, 'get_export_options_serializer'):
                    if plugin_serializer := export_plugin.get_export_options_serializer(
                        data=export_options
                    ):
                        plugin_serializer.is_valid(raise_exception=True)
                        export_context = plugin_serializer.validated_data

            user = getattr(request, 'user', None)

            # Add in extra context data for the plugin
            export_context['user'] = user

            # Create an output object to export against
            output = DataOutput.objects.create(
                user=user if user and user.is_authenticated else None,
                total=0,  # Note: this should get updated by the export task
                progress=0,
                complete=False,
                output_type=DataOutput.DataOutputTypes.EXPORT,
                plugin=export_plugin.slug,
                output=None,
            )

            # Offload the export task to a background worker
            # This is to avoid blocking the web server
            # Note: The export task will loop back and call the 'export_data' method on this class
            offload_task(
                data_exporter.tasks.export_data,
                self.__class__,
                request.user.id,
                request.query_params,
                plugin_slug,
                export_format,
                export_context,
                output.id,
                group='exporter',
            )

            output.refresh_from_db()

            # Return a response to the frontend
            return Response(DataOutputSerializer(output).data, status=200)

        return super().get(request, *args, **kwargs)
