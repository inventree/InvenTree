"""Mixin classes for data import/export functionality."""

from InvenTree.helpers import DownloadFile, GetExportFormats, current_date


class DataExportViewMixin:
    """Mixin class for exporting a dataset via the API.

    Adding this mixin to an API view allows the user to export the dataset to file in a variety of formats.

    We achieve this by overriding the 'get' method, and checking for the presence of the required query parameter.
    """

    EXPORT_QUERY_PARAMETER = 'export'

    def get_exported_filename(self, serializer, export_format):
        """Return the filename for the exported data file.

        An implementing class can override this implementation if required.
        """
        model = serializer.Meta.model
        date = current_date().isoformat()

        return f'InvenTree_{model.__name__}_{date}.{export_format}'

    def export_data(self, request, export_format):
        """Export the data in the specified format.

        Use the provided serializer to generate the data, and return it as a file download.
        """
        from importer.operations import export_data_to_file

        serializer = self.get_serializer_class()

        if not issubclass(serializer, DataExportSerializerMixin):
            raise TypeError(
                'Serializer class must inherit from DataExportSerialierMixin'
            )

        queryset = self.filter_queryset(self.get_queryset())

        filename = self.get_exported_filename(serializer, export_format)

        data_file = export_data_to_file(serializer, queryset, export_format)

        return DownloadFile(data_file, filename=filename)

    def get(self, request, *args, **kwargs):
        """Override the 'get' method to check for the export query parameter."""
        if export_format := request.query_params.get(self.EXPORT_QUERY_PARAMETER, None):
            export_format = str(export_format).strip().lower()
            if export_format in GetExportFormats():
                return self.export_data(request, export_format)

        # If the export query parameter is not present, return the default response
        return super().get(request, *args, **kwargs)


class DataImportSerializerMixin:
    """Mixin class for adding data import functionality to a DRF serializer."""

    import_only_fields = []
    import_exlude_fields = []

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
            # Exclude fields which are not required for data import
            for field in self.get_import_exclude_fields(**kwargs):
                self.fields.pop(field, None)
        else:
            # Exclude fields which are only used for data import
            for field in self.get_import_only_fields(**kwargs):
                self.fields.pop(field, None)


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


class DataImportExportSerializerMixin(
    DataImportSerializerMixin, DataExportSerializerMixin
):
    """Mixin class for adding data import/export functionality to a DRF serializer."""

    pass
