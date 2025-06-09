"""Custom exporter for PartParameters."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from part.models import Part
from part.serializers import PartSerializer
from plugin import InvenTreePlugin
from plugin.mixins import DataExportMixin


class PartParameterExportOptionsSerializer(serializers.Serializer):
    """Custom export options for the PartParameterExporter plugin."""

    export_stock_data = serializers.BooleanField(
        default=True, label=_('Stock Data'), help_text=_('Include part stock data')
    )

    export_pricing_data = serializers.BooleanField(
        default=True, label=_('Pricing Data'), help_text=_('Include part pricing data')
    )


class PartParameterExporter(DataExportMixin, InvenTreePlugin):
    """Builtin plugin for exporting PartParameter data.

    Extends the "part" export process, to include all associated PartParameter data.
    """

    NAME = 'Part Parameter Exporter'
    SLUG = 'parameter-exporter'
    TITLE = _('Part Parameter Exporter')
    DESCRIPTION = _('Exporter for part parameter data')
    VERSION = '1.0.0'
    AUTHOR = _('InvenTree contributors')

    ExportOptionsSerializer = PartParameterExportOptionsSerializer

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
        if not self.export_stock_data:
            # Remove stock data from the headers
            for field in [
                'allocated_to_build_orders',
                'allocated_to_sales_orders',
                'available_stock',
                'available_substitute_stock',
                'available_variant_stock',
                'building',
                'can_build',
                'external_stock',
                'in_stock',
                'on_order',
                'ordering',
                'required_for_build_orders',
                'required_for_sales_orders',
                'stock_item_count',
                'total_in_stock',
                'unallocated_stock',
                'variant_stock',
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

        # Add in a header for each part parameter
        for pk, name in self.parameters.items():
            headers[f'parameter_{pk}'] = str(name)

        return headers

    def prefetch_queryset(self, queryset):
        """Ensure that the part parameters are prefetched."""
        queryset = queryset.prefetch_related('parameters', 'parameters__template')

        return queryset

    def export_data(
        self, queryset, serializer_class, headers, context, output, **kwargs
    ):
        """Export part and parameter data."""
        # Extract custom serializer options and cache
        self.export_stock_data = context.get('export_stock_data', True)
        self.export_pricing_data = context.get('export_pricing_data', True)

        queryset = self.prefetch_queryset(queryset)
        self.serializer_class = serializer_class

        # Keep a dict of observed part parameters against their primary key
        self.parameters = {}

        # Serialize the queryset using DRF first
        parts = self.serializer_class(
            queryset, parameters=True, exporting=True, many=True
        ).data

        for part in parts:
            # Extract the part parameters from the serialized data
            for parameter in part.get('parameters', []):
                if template := parameter.get('template_detail', None):
                    template_id = template['pk']

                    if template_id not in self.parameters:
                        self.parameters[template_id] = template['name']

                    part[f'parameter_{template_id}'] = parameter['data']

        return parts
