"""Custom data exporter for part stocktake data."""

from decimal import Decimal

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from InvenTree.helpers import normalize
from part.models import Part
from part.serializers import PartSerializer
from plugin import InvenTreePlugin
from plugin.mixins import DataExportMixin


class PartStocktakeExportOptionsSerializer(serializers.Serializer):
    """Custom export options for the PartStocktakeExporter plugin."""

    export_pricing_data = serializers.BooleanField(
        default=True, label=_('Pricing Data'), help_text=_('Include part pricing data')
    )

    export_include_external_items = serializers.BooleanField(
        default=False,
        label=_('Include External Stock'),
        help_text=_('Include external stock in the stocktake data'),
    )

    export_include_variant_items = serializers.BooleanField(
        default=False,
        label=_('Include Variant Items'),
        help_text=_('Include part variant stock in stocktake data'),
    )

    export_exclude_zero_stock_entries = serializers.BooleanField(
        default=False,
        label=_('Exclude Zero Stock Entries'),
        help_text=_('Exclude parts with zero stock from the exported dataset'),
    )


class PartStocktakeExporter(DataExportMixin, InvenTreePlugin):
    """Builtin plugin for exporting part stocktake data.

    Extends the "part" export process, to include stocktake data.
    """

    NAME = 'Part Stocktake Exporter'
    SLUG = 'inventree-stocktake-exporter'
    TITLE = _('Part Stocktake Exporter')
    DESCRIPTION = _('Exporter for part stocktake data')
    VERSION = '1.1.0'
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

    def generate_filename(self, model_class, export_format: str) -> str:
        """Generate a filename for the exported part stocktake data."""
        from InvenTree.helpers import current_date

        date = current_date().isoformat()
        return f'InvenTree_Stocktake_{date}.{export_format}'

    def update_headers(self, headers, context, **kwargs):
        """Define headers for the Stocktake export."""
        export_pricing_data = context.get('export_pricing_data', True)
        include_external_items = context.get('export_include_external_items', True)
        include_variant_items = context.get('export_include_variant_items', False)

        # Use only a subset of fields from the PartSerializer
        base_headers = [
            'pk',
            'name',
            'IPN',
            'active',
            'component',
            'assembly',
            'description',
            'category',
            'allocated_to_build_orders',
            'allocated_to_sales_orders',
            'required_for_build_orders',
            'required_for_sales_orders',
            'ordering',
            'building',
            'scheduled_to_build',
            'external_stock',
            'variant_stock',
            'stock_item_count',
            'total_in_stock',
        ]

        if not include_external_items:
            base_headers.remove('external_stock')

        if not include_variant_items:
            base_headers.remove('variant_stock')

        stocktake_headers = {
            key: headers[key] for key in base_headers if key in headers
        }

        if export_pricing_data:
            stocktake_headers.update({
                'pricing_min': _('Minimum Unit Cost'),
                'pricing_max': _('Maximum Unit Cost'),
                'pricing_min_total': _('Minimum Total Cost'),
                'pricing_max_total': _('Maximum Total Cost'),
            })

        return stocktake_headers

    def prefetch_queryset(self, queryset):
        """Prefetch related data for the queryset."""
        return queryset.prefetch_related('stock_items')

    def export_data(
        self, queryset, serializer_class, headers, context, output, **kwargs
    ):
        """Export the data for the given queryset."""
        export_pricing_data = context.get('export_pricing_data', True)
        include_external_items = context.get('export_include_external_items', False)
        include_variant_items = context.get('export_include_variant_items', False)
        exclude_zero_stock = context.get('export_exclude_zero_stock_entries', False)

        data = super().export_data(
            queryset, serializer_class, headers, context, output, **kwargs
        )

        output_data = []

        for row in data:
            quantity = Decimal(row.get('total_in_stock', 0))

            if not include_external_items:
                quantity -= Decimal(row.get('external_stock', 0))

            if not include_variant_items:
                quantity -= Decimal(row.get('variant_stock', 0))

            if quantity < 0:
                quantity = Decimal(0)

                if exclude_zero_stock:
                    continue

            if export_pricing_data:
                pricing_min = row.get('pricing_min', None) or row.get(
                    'pricing_max', None
                )
                pricing_max = row.get('pricing_max', None) or row.get(
                    'pricing_min', None
                )

                if pricing_min is not None:
                    pricing_min = Decimal(pricing_min)
                    row['pricing_min_total'] = normalize(
                        pricing_min * quantity, rounding=10
                    )

                if pricing_max is not None:
                    pricing_max = Decimal(pricing_max)
                    row['pricing_max_total'] = normalize(
                        pricing_max * quantity, rounding=10
                    )

            output_data.append(row)

        return output_data
