"""The DigiKeyBarcodePlugin matches DigiKey barcodes to supplier parts."""

import logging

from django.utils.translation import gettext_lazy as _

from company.models import SupplierPart
from plugin import InvenTreePlugin
from plugin.mixins import BarcodeMixin
from .barcode2d import parse_ecia_barcode2d

logger = logging.getLogger('inventree')


class DigiKeyBarcodePlugin(BarcodeMixin, InvenTreePlugin):
    """BarcodePlugin for matching DigiKey barcodes."""

    NAME = "DigiKeyBarcode"
    TITLE = _("DigiKey Barcodes")
    DESCRIPTION = _("Provides support for scanning DigiKey barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    def scan(self, barcode_data):
        """Process a barcode to determine if it is a DigiKey barcode."""

        if not (barcode_fields := parse_ecia_barcode2d(barcode_data)):
            return

        if not (sku := barcode_fields.get("supplier_part_number")):
            return

        supplier_parts = SupplierPart.objects.filter(SKU__iexact=sku)
        if not supplier_parts or len(supplier_parts) > 1:
            logger.warning(
                f"Found {len(supplier_parts)} supplier parts for SKU "
                f"{sku} with DigiKeyBarcodePlugin plugin"
            )
            return
        supplier_part = supplier_parts[0]

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
                    f"DigiKeyBarcodePlugin plugin"
                )

        if order_number := barcode_fields.get("purchase_order_number"):
            data["order_number"] = order_number

        return {SupplierPart.barcode_model_type(): data}
