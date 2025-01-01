"""Plugin mixin class for DataExportMixin."""

from django.db.models.query import QuerySet
from django.http import StreamingHttpResponse

import tablib

from InvenTree.helpers import current_date


class DataExportMixin:
    """Mixin which allows custom data export functionality."""

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'DataExport'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('export', True, __class__)

    def filter_queryset(self, queryset: QuerySet, **kwargs) -> QuerySet:
        """Filter the queryset before exporting data.

        Arguments:
            queryset: The queryset to be filtered

        Returns:
            queryset: The filtered queryset

        Note: The default implementation simply returns the queryset as-is.
        """
        return queryset

    def process_row(self, row: dict, **kwargs) -> dict:
        """Process a single row of data for export.

        Arguments:
            row: The row of data to process (as a dictionary)

        Returns:
            dict: The processed row of data

        Note: The default implementation simply returns the row as-is.
        """
        return row

    def arrange_export_headers(self, headers: list, **kwargs) -> list:
        """Arrange the export headers before exporting the data.

        Arguments:
            headers: The list of headers to be exported

        Returns:
            list: The arranged list of headers

        Notes:
            - This method can be used to re-order or modify the headers before export.
            - The default implementation simply returns the headers as-is.
        """
        return headers

    def generate_records(self, queryset: QuerySet, serializer_class, **kwargs) -> list:
        """Generate a list of records to be exported."""
        # Export dataset with a second copy of the serializer
        # This is because when we pass many=True, the returned class is a ListSerializer
        return serializer_class(queryset, many=True, exporting=True).data

    def generate_filename(self, serializer_class, **kwargs) -> str:
        """Generate a filename for the exported data."""
        model = serializer_class.Meta.model
        date = current_date().isoformat()

        export_format = kwargs.get('fmt', 'csv')

        return f'InvenTree_{model.__name__}_{date}.{export_format}'

    def export_data(
        self, queryset: QuerySet, serializer_class, **kwargs
    ) -> StreamingHttpResponse:
        """Export the data in the specified format.

        Arguments:
            queryset: The queryset to export
            serializer_class: The serializer class to use for exporting the data

        Returns:
            StreamingHttpResponse: The exported data file

        Raises:
            ValidationError: If any of the inputs are invalid

        Note that this method should not need to be overridden in the child class,
        as is simply calls the other methods in the mixin.

        However, if a custom export method is required, this method can be overridden.
        """
        # Extract the export format from the provided kwargs
        fmt = kwargs.get('fmt', 'csv')

        # Pass queryset through the filter_queryset method
        # This allows for custom annotation, filtering, etc
        queryset = self.filter_queryset(queryset, **kwargs)

        serializer = serializer_class(exporting=True)
        serializer.initial_data = queryset

        fields = serializer.get_exportable_fields()

        field_names = self.arrange_export_headers(fields.keys())

        # Generate human-readable column names
        headers = []

        for field_name, field in fields.items():
            headers.append(serializer.get_field_label(field) or field_name)

        # Generate a tablib dataset
        dataset = tablib.Dataset(headers=headers)

        data = self.generate_records(queryset, serializer_class, **kwargs)

        for record in data:
            row = self.process_row(record, **kwargs)
            dataset.append([row.get(field, None) for field in field_names])

        return dataset.export(fmt)
