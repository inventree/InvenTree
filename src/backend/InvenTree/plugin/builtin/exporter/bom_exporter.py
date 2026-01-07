"""Multi-level BOM exporter plugin."""

from decimal import Decimal
from typing import Optional

from django.utils.translation import gettext_lazy as _

import rest_framework.serializers as serializers

from InvenTree.helpers import normalize
from part.models import BomItem
from part.serializers import BomItemSerializer
from plugin import InvenTreePlugin
from plugin.mixins import DataExportMixin


class BomExporterOptionsSerializer(serializers.Serializer):
    """Custom export options for the BOM exporter plugin."""

    export_levels = serializers.IntegerField(
        default=0,
        label=_('Levels'),
        help_text=_(
            'Number of levels to export - set to zero to export all BOM levels'
        ),
        min_value=0,
    )

    export_total_quantity = serializers.BooleanField(
        default=True,
        label=_('Total Quantity'),
        help_text=_('Include total quantity of each part in the BOM'),
    )

    export_stock_data = serializers.BooleanField(
        default=True, label=_('Stock Data'), help_text=_('Include part stock data')
    )

    export_pricing_data = serializers.BooleanField(
        default=True, label=_('Pricing Data'), help_text=_('Include part pricing data')
    )

    export_supplier_data = serializers.BooleanField(
        default=True, label=_('Supplier Data'), help_text=_('Include supplier data')
    )

    export_manufacturer_data = serializers.BooleanField(
        default=True,
        label=_('Manufacturer Data'),
        help_text=_('Include manufacturer data'),
    )

    export_substitute_data = serializers.BooleanField(
        default=True,
        label=_('Substitute Data'),
        help_text=_('Include substitute part data'),
    )

    export_parameter_data = serializers.BooleanField(
        default=True,
        label=_('Parameter Data'),
        help_text=_('Include part parameter data'),
    )


class BomExporterPlugin(DataExportMixin, InvenTreePlugin):
    """Builtin plugin for performing multi-level BOM exports."""

    NAME = 'BOM Exporter'
    SLUG = 'bom-exporter'
    TITLE = _('Multi-Level BOM Exporter')
    DESCRIPTION = _('Provides support for exporting multi-level BOMs')
    VERSION = '1.1.0'
    AUTHOR = _('InvenTree contributors')

    ExportOptionsSerializer = BomExporterOptionsSerializer

    def supports_export(self, model_class: type, user, *args, **kwargs) -> bool:
        """This exported only supports the BomItem model."""
        return (
            model_class == BomItem
            and kwargs.get('serializer_class') == BomItemSerializer
        )

    def update_headers(self, headers, context, **kwargs):
        """Update headers for the BOM export."""
        export_total_quantity = context.get('export_total_quantity', True)

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

        if export_total_quantity:
            # Append a 'total quantity' field
            headers['total_quantity'] = _('Total Quantity')

        # Append variant part columns
        if self.export_substitute_data and self.n_substitute_cols > 0:
            for idx in range(self.n_substitute_cols):
                n = idx + 1
                headers[f'substitute_{idx}'] = _(f'Substitute {n}')

        # Append supplier part columns
        if self.export_supplier_data and self.n_supplier_cols > 0:
            for idx in range(self.n_supplier_cols):
                n = idx + 1
                headers[f'supplier_name_{idx}'] = _(f'Supplier {n}')
                headers[f'supplier_sku_{idx}'] = _(f'Supplier {n} SKU')
                headers[f'supplier_mpn_{idx}'] = _(f'Supplier {n} MPN')

        # Append manufacturer part columns
        if self.export_manufacturer_data and self.n_manufacturer_cols > 0:
            for idx in range(self.n_manufacturer_cols):
                n = idx + 1
                headers[f'manufacturer_name_{idx}'] = _(f'Manufacturer {n}')
                headers[f'manufacturer_mpn_{idx}'] = _(f'Manufacturer {n} MPN')

        # Append part parameter columns
        if self.export_parameter_data and len(self.parameters) > 0:
            for key, value in self.parameters.items():
                headers[f'parameter_{key}'] = value

        return headers

    def prefetch_queryset(self, queryset):
        """Perform pre-fetch on the provided queryset."""
        queryset = queryset.prefetch_related('sub_part')

        if self.export_substitute_data:
            queryset = queryset.prefetch_related('substitutes')

        if self.export_supplier_data:
            queryset = queryset.prefetch_related(
                'sub_part__supplier_parts',
                'sub_part__supplier_parts__supplier',
                'sub_part__supplier_parts__manufacturer_part',
                'sub_part__supplier_parts__manufacturer_part__manufacturer',
            )

        if self.export_manufacturer_data:
            queryset = queryset.prefetch_related(
                'sub_part__manufacturer_parts',
                'sub_part__manufacturer_parts__manufacturer',
            )

        if self.export_parameter_data:
            queryset = queryset.prefetch_related(
                'sub_part__parameters_list', 'sub_part__parameters_list__template'
            )

        return queryset

    def export_data(
        self, queryset, serializer_class, headers, context, output, **kwargs
    ):
        """Export BOM data from the queryset."""
        self.serializer_class = serializer_class

        # Track how many extra columns we need
        self.n_substitute_cols = 0
        self.n_supplier_cols = 0
        self.n_manufacturer_cols = 0

        # A dict of "Parameter ID" -> "Parameter Name"
        self.parameters = {}

        # Extract the export options from the context (and cache for later)
        self.export_levels = context.get('export_levels', 1)
        self.export_stock_data = context.get('export_stock_data', True)
        self.export_pricing_data = context.get('export_pricing_data', True)
        self.export_supplier_data = context.get('export_supplier_data', True)
        self.export_manufacturer_data = context.get('export_manufacturer_data', True)
        self.export_substitute_data = context.get('export_substitute_data', True)
        self.export_parameter_data = context.get('export_parameter_data', True)
        self.export_total_quantity = context.get('export_total_quantity', True)

        # Pre-fetch related data to reduce database queries
        queryset = self.prefetch_queryset(queryset)

        self.bom_data = []

        # Run through each item in the queryset
        for bom_item in queryset:
            self.process_bom_row(bom_item, 1, **kwargs)

        return self.bom_data

    def process_bom_row(
        self, bom_item, level: int = 1, multiplier: Optional[Decimal] = None, **kwargs
    ) -> list:
        """Process a single BOM row.

        Arguments:
            bom_item: The BomItem object to process
            level: The current level of export
            multiplier: The multiplier for the quantity (used for recursive calls)
        """
        # Add this row to the output dataset
        row = self.serializer_class(bom_item, exporting=True).data
        row['level'] = level

        if multiplier is None:
            multiplier = Decimal(1)

        # Extend with additional data

        if self.export_substitute_data:
            row.update(self.get_substitute_data(bom_item))

        if self.export_supplier_data:
            row.update(self.get_supplier_data(bom_item))

        if self.export_manufacturer_data:
            row.update(self.get_manufacturer_data(bom_item))

        if self.export_parameter_data:
            row.update(self.get_parameter_data(bom_item))

        if self.export_total_quantity:
            # Calculate the total quantity for this BOM item
            total_quantity = Decimal(bom_item.quantity) * multiplier
            row['total_quantity'] = normalize(total_quantity)

        self.bom_data.append(row)

        # If we have reached the maximum export level, return just this bom item
        if bom_item.sub_part.assembly and (
            self.export_levels <= 0 or level < self.export_levels
        ):
            sub_items = bom_item.sub_part.get_bom_items()
            sub_items = self.prefetch_queryset(sub_items)
            sub_items = BomItemSerializer.annotate_queryset(sub_items)

            for item in sub_items.all():
                self.process_bom_row(
                    item,
                    level=level + 1,
                    multiplier=multiplier * bom_item.quantity,
                    **kwargs,
                )

    def get_substitute_data(self, bom_item: BomItem) -> dict:
        """Return substitute part data for a BomItem."""
        substitute_part_data = {}

        idx = 0

        for substitute in bom_item.substitutes.all():
            substitute_part_data.update({f'substitute_{idx}': substitute.part.name})

            idx += 1

        self.n_substitute_cols = max(self.n_substitute_cols, idx)

        return substitute_part_data

    def get_supplier_data(self, bom_item: BomItem) -> dict:
        """Return supplier and manufacturer data for a BomItem."""
        supplier_part_data = {}

        idx = 0

        for supplier_part in bom_item.sub_part.supplier_parts.all():
            manufacturer_part = supplier_part.manufacturer_part
            supplier_part_data.update({
                f'supplier_name_{idx}': supplier_part.supplier.name
                if supplier_part.supplier
                else '',
                f'supplier_sku_{idx}': supplier_part.SKU,
                f'supplier_mpn_{idx}': manufacturer_part.MPN
                if manufacturer_part
                else '',
            })

            idx += 1

        self.n_supplier_cols = max(self.n_supplier_cols, idx)

        return supplier_part_data

    def get_manufacturer_data(self, bom_item: BomItem) -> dict:
        """Return manufacturer data for a BomItem."""
        manufacturer_part_data = {}

        idx = 0

        for manufacturer_part in bom_item.sub_part.manufacturer_parts.all():
            manufacturer_part_data.update({
                f'manufacturer_name_{idx}': manufacturer_part.manufacturer.name
                if manufacturer_part.manufacturer
                else '',
                f'manufacturer_mpn_{idx}': manufacturer_part.MPN,
            })

            idx += 1

        self.n_manufacturer_cols = max(self.n_manufacturer_cols, idx)

        return manufacturer_part_data

    def get_parameter_data(self, bom_item: BomItem) -> dict:
        """Return parameter data for a BomItem."""
        parameter_data = {}

        for parameter in bom_item.sub_part.parameters.all():
            template = parameter.template
            if template.pk not in self.parameters:
                self.parameters[template.pk] = template.name

            parameter_data.update({f'parameter_{template.pk}': parameter.data})

        return parameter_data
