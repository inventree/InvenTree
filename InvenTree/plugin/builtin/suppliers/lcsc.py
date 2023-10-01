"""The LCSCPlugin is meant to integrate the LCSC API into Inventree.

This plugin can currently only match LCSC barcodes to supplier parts.
"""

import logging
import re

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import SupplierBarcodeMixin

logger = logging.getLogger('inventree')


class LCSCPlugin(SupplierBarcodeMixin, InvenTreePlugin):
    """Plugin to integrate the LCSC API into Inventree."""

    NAME = "LCSCPlugin"
    TITLE = _("Supplier Integration - LCSC")
    DESCRIPTION = _("Provides support for scanning LCSC barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    def parse_supplier_barcode_data(self, barcode_data):
        """Get supplier_part and barcode_fields from LCSC QR-Code."""

        if not isinstance(barcode_data, str):
            return None

        if not (match := LCSC_BARCODE_REGEX.fullmatch(barcode_data)):
            return None

        barcode_pairs = (pair.split(":") for pair in match.group(1).split(","))
        barcode_fields = {
            BARCODE_FIELD_NAME_MAP.get(field_name, field_name): value
            for field_name, value in barcode_pairs
        }

        sku = barcode_fields.get("supplier_part_number")
        if not (supplier_part := self.get_supplier_part(sku)):
            return None

        return supplier_part, barcode_fields


LCSC_BARCODE_REGEX = re.compile(r"^{((?:[^:,]+:[^:,]*,)*(?:[^:,]+:[^:,]*))}$")
BARCODE_FIELD_NAME_MAP = {
    "pc": "supplier_part_number",
    "on": "purchase_order_number",
    "pm": "manufacturer_part_number",
    "qty": "quantity",
}
