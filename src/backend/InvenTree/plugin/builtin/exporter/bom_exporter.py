"""Multi-level BOM exporter plugin."""

from django.utils.translation import gettext_lazy as _

import rest_framework.serializers as serializers

from part.models import BomItem
from plugin import InvenTreePlugin
from plugin.mixins import DataExportMixin, SettingsMixin


class BomExporterOptionsSerializer(serializers.Serializer):
    """Custom export options for the BOM exporter plugin."""

    export_levels = serializers.IntegerField(
        default=1,
        label=_('Levels'),
        help_text=_('Number of levels to export'),
        min_value=0,
    )

    export_stock_data = serializers.BooleanField(
        default=True,
        label=_('Stock Data'),
        help_text=_('Include current stock data in the export'),
    )

    export_pricing_data = serializers.BooleanField(
        default=True,
        label=_('Pricing Data'),
        help_text=_('Include pricing data in the export'),
    )

    export_supplier_data = serializers.BooleanField(
        default=True,
        label=_('Supplier Data'),
        help_text=_('Include supplier data in the export'),
    )

    export_manufacturer_data = serializers.BooleanField(
        default=True,
        label=_('Manufacturer Data'),
        help_text=_('Include manufacturer data in the export'),
    )

    export_substitute_data = serializers.BooleanField(
        default=True,
        label=_('Substitute Data'),
        help_text=_('Include substitute part data in the export'),
    )


class BomExporterPlugin(DataExportMixin, SettingsMixin, InvenTreePlugin):
    """Builtin plugin for performing multi-level BOM exports."""

    NAME = 'BOM Exporter'
    SLUG = 'bom-exporter'
    TITLE = _('InvenTree BOM exporter')
    DESCRIPTION = _('Provides support for exporting multi-level BOMs')
    VERSION = '1.0.0'
    AUTHOR = _('InvenTree contributors')

    SETTINGS = {}

    ExportOptionsSerializer = BomExporterOptionsSerializer

    def supports_export(self, model_class: type, user, *args, **kwargs) -> bool:
        """This exported only supports the BomItem model."""
        return model_class == BomItem

    def update_headers(self, headers, context, **kwargs):
        """Update headers for the BOM export."""
        if not self.export_stock_data:
            # Remove stock data from the headers
            for field in [
                'available_stock',
                'available_substitute_stock',
                'available_variant_stock',
                'external_stock',
                'on_order',
                'building',
                'can_build',
            ]:
                headers.pop(field, None)

        if not self.export_pricing_data:
            # Remove pricing data from the headers
            for field in [
                'pricing_min',
                'pricing_max',
                'pricing_min_total',
                'pricing_max_total',
                'pricing_updated',
            ]:
                headers.pop(field, None)

        # Append a "BOM Level" field
        headers['level'] = _('BOM Level')

        return headers

    def export_data(self, queryset, serializer_class, headers, context, **kwargs):
        """Export BOM data from the queryset."""
        self.serializer_class = serializer_class

        # Extract the export options from the context (and cache for later)
        self.export_levels = context.get('export_levels', 1)
        self.export_stock_data = context.get('export_stock_data', True)
        self.export_pricing_data = context.get('export_pricing_data', True)
        self.export_supplier_data = context.get('export_supplier_data', True)
        self.export_manufacturer_data = context.get('export_manufacturer_data', True)
        self.export_substitute_data = context.get('export_substitute_data', True)

        # Pre-fetch related data to reduce database queries
        if self.export_supplier_data:
            queryset = queryset.prefetch_related('sub_part__supplier_parts')

        if self.export_manufacturer_data:
            queryset = queryset.prefetch_related('sub_part__manufacturer_parts')

        self.bom_data = []

        # Run through each item in the queryset
        for bom_item in queryset:
            self.process_bom_row(bom_item, 1, **kwargs)

        return self.bom_data

    def process_bom_row(self, bom_item, level, **kwargs) -> list:
        """Process a single BOM row.

        Arguments:
            bom_item: The BomItem object to process
            level: The current level of export

        """
        # Add this row to the output dataset
        row = self.serializer_class(bom_item, exporting=True).data
        row['level'] = level
        self.bom_data.append(row)

        # If we have reached the maximum export level, return just this bom item
        if bom_item.sub_part.assembly and (
            self.export_levels <= 0 or level < self.export_levels
        ):
            for item in bom_item.sub_part.get_bom_items():
                self.process_bom_row(item, level + 1, **kwargs)
