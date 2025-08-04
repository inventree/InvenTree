"""Custom data exporter for part stocktake data."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from part.models import Part
from part.serializers import PartSerializer
from plugin import InvenTreePlugin
from plugin.mixins import DataExportMixin


class PartStocktakeExportOptionsSerializer(serializers.Serializer):
    """Custom export options for the PartStocktakeExporter plugin."""

    export_pricing_data = serializers.BooleanField(
        default=True, label=_('Pricing Data'), help_text=_('Include part pricing data')
    )


class PartStocktakeExporter(DataExportMixin, InvenTreePlugin):
    """Builtin plugin for exporting part stocktake data.

    Extends the "part" export process, to include stocktake data.
    """

    NAME = 'Part Stocktake Exporter'
    SLUG = 'stocktake-exporter'
    TITLE = _('Part Stocktake Exporter')
    DESCRIPTION = _('Exporter for part stocktake data')
    VERSION = '1.0.0'
    AUTHOR = _('InvenTree contributors')

    ExportOptionsSerializer = PartStocktakeExportOptionsSerializer

    def supports_export(
        self,
        model_class: type,
        user=None,
        serializer_class=None,
        view_class=None,
        *args,
        **kwargs,
    ) -> bool:
        """Supported if the base model is Part."""
        return model_class == Part and serializer_class == PartSerializer

    def update_headers(self, headers, context, **kwargs):
        """Update headers for the export."""
        # Add in the 'stocktake' headers
        headers['stock_items'] = _('Stock Items')
        headers['total_stock'] = _('Total Stock')
        headers['minimum_cost'] = _('Minimum Cost')
        headers['maximum_cost'] = _('Maximum Cost')

        return headers

    def prefetch_queryset(self, queryset):
        """Prefetch related data for the queryset."""
        # TODO
        return queryset

    def export_data(
        self, queryset, serializer_class, headers, context, output, **kwargs
    ):
        """Export the data for the given queryset."""
        print('=== export_data ===')
        return super().export_data(
            queryset, serializer_class, headers, context, output, **kwargs
        )
