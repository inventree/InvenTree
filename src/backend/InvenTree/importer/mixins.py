"""Mixin classes for data import/export functionality."""

from InvenTree.helpers import DownloadFile, GetExportFormats, current_date


class DataExportMixin:
    """Mixin class for exporting a dataset via the API.

    Adding this mixin to an API view allows the user to export the dataset to file in a variety of formats.

    We achieve this by overriding the 'get' method, and checking for the presence of the required query parameter.
    """

    EXPORT_QUERY_PARAMETER = 'export2'

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
