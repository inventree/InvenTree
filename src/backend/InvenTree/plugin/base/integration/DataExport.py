"""Plugin class for custom data exporting."""

from collections import OrderedDict


class DataExportMixin:
    """Mixin which provides ability to customize data exports.

    When exporting data from the API, this mixin can be used to provide
    custom data export functionality.
    """

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'DataExport'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('exporter', True, __class__)

    def update_headers(self, headers: OrderedDict, **kwargs) -> OrderedDict:
        """Update the headers for the data export.

        Allows for optional modification of the headers for the data export.

        Args:
            headers: The current headers for the export
            kwargs: Additional keyword arguments

        Returns: The updated headers
        """
        # The default implementation does nothing
        return headers

    def export_data(self, queryset, serializer_class, headers: OrderedDict, **kwargs):
        """Export data from the queryset.

        This method should be implemented by the plugin to provide
        the actual data export functionality.

        Args:
            queryset: The queryset to export
            headers: The headers for the export
            kwargs: Additional keyword arguments

        Returns: The exported data
        """
        raise NotImplementedError('export_data method must be implemented by plugin!')
