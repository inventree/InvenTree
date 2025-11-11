"""Plugin class for custom data exporting."""

from collections import OrderedDict
from typing import Optional

from django.contrib.auth.models import User
from django.db.models import QuerySet

from rest_framework import serializers, views

from common.models import DataOutput
from InvenTree.helpers import current_date
from plugin import PluginMixinEnum


class DataExportMixin:
    """Mixin which provides ability to customize data exports.

    When exporting data from the API, this mixin can be used to provide
    custom data export functionality.
    """

    ExportOptionsSerializer = None

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'DataExport'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin(PluginMixinEnum.EXPORTER, True, __class__)

    def supports_export(
        self,
        model_class: type,
        user: User,
        serializer_class: Optional[serializers.Serializer] = None,
        view_class: Optional[views.APIView] = None,
        *args,
        **kwargs,
    ) -> bool:
        """Return True if this plugin supports exporting data for the given model.

        Args:
            model_class: The model class to check
            user: The user requesting the export
            serializer_class: The serializer class to use for exporting the data
            view_class: The view class to use for exporting the data

        Returns:
            True if the plugin supports exporting data for the given model
        """
        # By default, plugins support all models
        return True

    def generate_filename(self, model_class, export_format: str) -> str:
        """Generate a filename for the exported data."""
        model = model_class.__name__
        date = current_date().isoformat()

        return f'InvenTree_{model}_{date}.{export_format}'

    def update_headers(
        self, headers: OrderedDict, context: dict, **kwargs
    ) -> OrderedDict:
        """Update the headers for the data export.

        Allows for optional modification of the headers for the data export.

        Arguments:
            headers: The current headers for the export
            context: The context for the export (provided by the plugin serializer)

        Returns: The updated headers
        """
        # The default implementation does nothing
        return headers

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        """Filter the queryset before exporting data."""
        # The default implementation returns the queryset unchanged
        return queryset

    def export_data(
        self,
        queryset: QuerySet,
        serializer_class: serializers.Serializer,
        headers: OrderedDict,
        context: dict,
        output: DataOutput,
        **kwargs,
    ) -> list:
        """Export data from the queryset.

        This method should be implemented by the plugin to provide
        the actual data export functionality.

        Arguments:
            queryset: The queryset to export
            serializer_class: The serializer class to use for exporting the data
            headers: The headers for the export
            context: Any custom context for the export (provided by the plugin serializer)
            output: The DataOutput object for the export

        Returns: The exported data (a list of dict objects)
        """
        # The default implementation simply serializes the queryset
        return serializer_class(queryset, many=True, exporting=True).data

    def get_export_options_serializer(self, **kwargs) -> serializers.Serializer | None:
        """Return a serializer class with dynamic export options for this plugin.

        Returns:
            A class instance of a DRF serializer class, by default this an instance of
            self.ExportOptionsSerializer using the *args, **kwargs if existing for this plugin
        """
        # By default, look for a class level attribute
        serializer = getattr(self, 'ExportOptionsSerializer', None)

        if serializer:
            return serializer(**kwargs)
