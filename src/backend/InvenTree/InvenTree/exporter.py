"""Code mixins for exporting data via the API."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import tablib
from rest_framework import serializers
from taggit.serializers import TagListSerializerField

from InvenTree.helpers import DownloadFile, GetExportFormats, current_date
from plugin.registry import registry


class DataExportSerializerMixin:
    """Mixin class for adding data export functionality to a DRF serializer.

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

    def get_exported_filename(self, export_format) -> str:
        """Return the filename for the exported data file.

        An implementing class can override this implementation if required.

        Arguments:
            export_format: The file format to be exported

        Returns:
            str: The filename for the exported file
        """
        model = self.Meta.model
        date = current_date().isoformat()

        return f'InvenTree_{model.__name__}_{date}.{export_format}'

    @classmethod
    def arrange_export_headers(cls, headers: list) -> list:
        """Optional method to arrange the export headers."""
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

    def process_row(self, row):
        """Optional method to process a row before exporting it."""
        return row

    def export_to_file(self, data, file_format):
        """Export the queryset to a file in the specified format.

        Arguments:
            queryset: The queryset to export
            data: The serialized dataset to export
            file_format: The file format to export to

        Returns:
            File object containing the exported data
        """
        # Extract all exportable fields from this serializer
        fields = self.get_exportable_fields()

        field_names = self.arrange_export_headers(list(fields.keys()))

        # Extract human-readable field names
        headers = []

        for field_name, field in fields.items():
            field = fields[field_name]

            label = getattr(field, 'label', field_name)

            if parent := getattr(field, 'parent_field', None):
                label = f'{parent.label}.{label}'

            headers.append(label)

        dataset = tablib.Dataset(headers=headers)

        for row in data:
            row = self.process_row(row)
            dataset.append([self.get_nested_value(row, f) for f in field_names])

        return dataset.export(file_format)


class DataExportViewMixin:
    """An API view mixin for directly exporting selected data.

    Adding this mixin to an API view allows the user to export the dataset to file in a variety of formats.

    We achieve this by overriding the 'get' method, and checking for the presence of the required query parameter.
    """

    EXPORT_QUERY_PARAMETER = 'export'

    def export_data(self, export_format, plugin=None):
        """Export the data in the specified format.

        Arguments:
            export_format: The file format to export the data in
            plugin: The name of the plugin to use for exporting the data

        - By default, uses the provided serializer to generate the data, and return it as a file download.
        - If a plugin is specified, the plugin can be used to augment or replace the export functionality.
        """
        serializer_class = self.get_serializer_class()

        if not issubclass(serializer_class, DataExportSerializerMixin):
            raise TypeError(
                'Serializer class must inherit from DataExportSerialierMixin'
            )

        queryset = self.filter_queryset(self.get_queryset())

        serializer = serializer_class(exporting=True)
        serializer.initial_data = queryset

        # Export dataset with a second copy of the serializer
        # This is because when we pass many=True, the returned class is a ListSerializer
        data = serializer_class(queryset, many=True, exporting=True).data

        filename = serializer.get_exported_filename(export_format)
        datafile = serializer.export_to_file(data, export_format)

        return DownloadFile(datafile, filename=filename)

    def get(self, request, *args, **kwargs):
        """Override the 'get' method to check for the export query parameter."""
        if export_format := request.query_params.get(self.EXPORT_QUERY_PARAMETER, None):
            export_format = str(export_format).strip().lower()

            # Check if a data export plugin is specified
            plugin_slug = request.query_params.get('plugin', None)

            plugin = registry.get_plugin(
                plugin_slug, active=True, with_mixin='exporter'
            )

            if export_format in GetExportFormats():
                return self.export_data(export_format, plugin=plugin)
            else:
                raise ValidationError({
                    self.EXPORT_QUERY_PARAMETER: _('Invalid export format')
                })

        # If the export query parameter is not present, return the default response
        return super().get(request, *args, **kwargs)
