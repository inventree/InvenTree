"""The MouserBarcodePlugin matches Mouser barcodes to supplier parts."""

import logging

from django.utils.translation import gettext_lazy as _

from company.models import ManufacturerPart, SupplierPart
from plugin import InvenTreePlugin, registry
from plugin.mixins import BarcodeMixin, SettingsMixin
from .barcode2d import parse_ecia_barcode2d

logger = logging.getLogger('inventree')


class MouserBarcodePlugin(BarcodeMixin, SettingsMixin, InvenTreePlugin):
    """BarcodePlugin for matching Mouser barcodes."""

    NAME = "MouserBarcode"
    TITLE = _("Mouser Barcodes")
    DESCRIPTION = _("Provides support for scanning Mouser barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    SETTINGS = {
        "MOUSER_SUPPLIER_NAME": {
            "name": _("Mouser Supplier Name"),
            "description": _("Name of the Supplier which acts as 'Mouser'"),
            "default": "Mouser",
            "validator": lambda name: bool(name),
        }
    }

    def scan(self, barcode_data):
        """Process a barcode to determine if it is a Mouser barcode."""

        if not (barcode_fields := parse_ecia_barcode2d(barcode_data)):
            return

        if sku := barcode_fields.get("supplier_part_number"):
            supplier_parts = SupplierPart.objects.filter(SKU__iexact=sku)
            if not supplier_parts or len(supplier_parts) > 1:
                logger.warning(
                    f"Found {len(supplier_parts)} supplier parts for SKU "
                    f"{sku} with MouserBarcodePlugin plugin"
                )
                return
            supplier_part = supplier_parts[0]
        elif mpn := barcode_fields.get("manufacturer_part_number"):
            manufacturer_parts = ManufacturerPart.objects.filter(
                MPN__iexact=mpn)
            if not manufacturer_parts or len(manufacturer_parts) > 1:
                logger.warning(
                    f"Found {len(manufacturer_parts)} manufacturer parts for "
                    f"MPN {mpn} with MouserBarcodePlugin plugin"
                )
                return
            manufacturer_part = manufacturer_parts[0]

            supplier_name = self.get_setting("MOUSER_SUPPLIER_NAME")
            supplier_parts = SupplierPart.objects.filter(
                manufacturer_part=manufacturer_part.pk,
                supplier__name__iexact=supplier_name)
            if not supplier_parts or len(supplier_parts) > 1:
                logger.warning(
                    f"Found {len(supplier_parts)} supplier parts for SKU "
                    f"{sku} and supplier '{supplier_name}' with "
                    f"MouserBarcodePlugin plugin"
                )
                return
            supplier_part = supplier_parts[0]
        else:
            return

        data = {
            "pk": supplier_part.pk,
            "api_url": f"{SupplierPart.get_api_url()}{supplier_part.pk}/",
            "web_url": supplier_part.get_absolute_url(),
        }

        if quantity := barcode_fields.get("quantity"):
            try:
                data["quantity"] = int(quantity)
            except ValueError:
                logger.warning(
                    f"Failed to parse quantity '{quantity}' with "
                    f"MouserBarcodePlugin plugin"
                )

        if order_number := barcode_fields.get("purchase_order_number"):
            data["order_number"] = order_number

        return {SupplierPart.barcode_model_type(): data}
