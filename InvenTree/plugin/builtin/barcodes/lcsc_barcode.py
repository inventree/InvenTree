"""The LCSCBarcodePlugin matches LCSC barcodes to supplier parts."""

import logging, re

from django.utils.translation import gettext_lazy as _

from company.models import SupplierPart
from plugin import InvenTreePlugin
from plugin.mixins import BarcodeMixin

logger = logging.getLogger('inventree')

LCSC_BARCODE_REGEX = re.compile(r"^{((?:[^:,]+:[^:,]*,)*(?:[^:,]+:[^:,]*))}$")
BARCODE_FIELD_NAME_MAP = {
    "pc": "supplier_part_number",
    "on": "purchase_order_number",
    "pm": "manufacturer_part_number",
    "qty": "quantity",
}


class LCSCBarcodePlugin(BarcodeMixin, InvenTreePlugin):
    """BarcodePlugin for matching LCSC barcodes."""

    NAME = "LCSCBarcode"
    TITLE = _("LCSC Barcodes")
    DESCRIPTION = _("Provides support for scanning LCSC barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    def scan(self, barcode_data):
        """Process a barcode to determine if it is a LCSC barcode."""

        if not (match := LCSC_BARCODE_REGEX.fullmatch(barcode_data)):
            return

        barcode_pairs = (pair.split(":") for pair in match.group(1).split(","))
        barcode_fields = {
            BARCODE_FIELD_NAME_MAP.get(field_name, field_name): value
            for field_name, value in barcode_pairs
        }

        if not (sku := barcode_fields.get("supplier_part_number")):
            return

        supplier_parts = SupplierPart.objects.filter(SKU__iexact=sku)
        if not supplier_parts or len(supplier_parts) > 1:
            logger.warning(
                f"Found {len(supplier_parts)} supplier parts for SKU "
                f"{sku} with LCSCBarcodePlugin plugin"
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
                    f"LCSCBarcodePlugin plugin"
                )

        if order_number := barcode_fields.get("purchase_order_number"):
            data["order_number"] = order_number

        return {SupplierPart.barcode_model_type(): data}
