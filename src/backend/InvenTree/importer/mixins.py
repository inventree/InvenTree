"""Mixin classes for data import/export functionality."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import tablib
from rest_framework import fields, serializers

import importer.operations
from InvenTree.helpers import DownloadFile, GetExportFormats, current_date


class DataImportSerializerMixin:
    """Mixin class for adding data import functionality to a DRF serializer."""

    import_only_fields = []
    import_exclude_fields = []

    def get_import_only_fields(self, **kwargs) -> list:
        """Return the list of field names which are only used during data import."""
        return self.import_only_fields

    def get_import_exclude_fields(self, **kwargs) -> list:
        """Return the list of field names which are excluded during data import."""
        return self.import_exclude_fields

    def __init__(self, *args, **kwargs):
        """Initialise the DataImportSerializerMixin.

        Determine if the serializer is being used for data import,
        and if so, adjust the serializer fields accordingly.
        """
        importing = kwargs.pop('importing', False)

        super().__init__(*args, **kwargs)

        if importing:
            # Exclude any fields which are not able to be imported
            importable_field_names = list(self.get_importable_fields().keys())
            field_names = list(self.fields.keys())

            for field in field_names:
                if field not in importable_field_names:
                    self.fields.pop(field, None)

            # Exclude fields which are excluded for data import
            for field in self.get_import_exclude_fields(**kwargs):
                self.fields.pop(field, None)

        else:
            # Exclude fields which are only used for data import
            for field in self.get_import_only_fields(**kwargs):
                self.fields.pop(field, None)

    def get_importable_fields(self) -> dict:
        """Return a dict of fields which can be imported against this serializer instance.

        Returns:
            dict: A dictionary of field names and field objects
        """
        importable_fields = {}

        if meta := getattr(self, 'Meta', None):
            read_only_fields = getattr(meta, 'read_only_fields', [])
        else:
            read_only_fields = []

        for name, field in self.fields.items():
            # Skip read-only fields
            if getattr(field, 'read_only', False):
                continue

            if name in read_only_fields:
                continue

            # Skip fields which are themselves serializers
            if issubclass(field.__class__, serializers.Serializer):
                continue

            # Skip file fields
            if issubclass(field.__class__, fields.FileField):
                continue

            importable_fields[name] = field

        return importable_fields


class DataExportSerializerMixin:
    """Mixin class for adding data export functionality to a DRF serializer."""

    export_only_fields = []
    export_exclude_fields = []

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
            if getattr(field, 'write_only', False):
                continue

            if name in write_only_fields:
                continue

            # Skip fields which are themselves serializers
            if issubclass(field.__class__, serializers.Serializer):
                continue

            fields[name] = field

        return fields

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

            headers.append(importer.operations.get_field_label(field) or field_name)

        dataset = tablib.Dataset(headers=headers)

        for row in data:
            row = self.process_row(row)
            dataset.append([row.get(field, None) for field in field_names])

        return dataset.export(file_format)


class DataImportExportSerializerMixin(
    DataImportSerializerMixin, DataExportSerializerMixin
):
    """Mixin class for adding data import/export functionality to a DRF serializer."""


class DataExportViewMixin:
    """Mixin class for exporting a dataset via the API.

    Adding this mixin to an API view allows the user to export the dataset to file in a variety of formats.

    We achieve this by overriding the 'get' method, and checking for the presence of the required query parameter.
    """

    EXPORT_QUERY_PARAMETER = 'export'

    def export_data(self, export_format):
        """Export the data in the specified format.

        Use the provided serializer to generate the data, and return it as a file download.
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
            if export_format in GetExportFormats():
                return self.export_data(export_format)
            else:
                raise ValidationError({
                    self.EXPORT_QUERY_PARAMETER: _('Invalid export format')
                })

        # If the export query parameter is not present, return the default response
        return super().get(request, *args, **kwargs)
