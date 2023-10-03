"""The TMEPlugin is meant to integrate the TME API into Inventree.

This plugin can currently only match TME barcodes to supplier parts.
"""

import logging
import re

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import SupplierBarcodeMixin

logger = logging.getLogger('inventree')


class TMEPlugin(SupplierBarcodeMixin, InvenTreePlugin):
    """Plugin to integrate the TME API into Inventree."""

    NAME = "TMEPlugin"
    TITLE = _("Supplier Integration - TME")
    DESCRIPTION = _("Provides support for scanning TME barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    def parse_supplier_barcode_data(self, barcode_data):
        """Get supplier_part and barcode_fields from TME QR-Code or DataMatrix-Code."""

        if not isinstance(barcode_data, str):
            return None

        if TME_IS_QRCODE_REGEX.fullmatch(barcode_data):
            barcode_fields = {
                QRCODE_FIELD_NAME_MAP.get(field_name, field_name): value
                for field_name, value in TME_PARSE_QRCODE_REGEX.findall(barcode_data)
            }
        elif barcode_split := TME_PARSE_BARCODE2D_REGEX.findall(barcode_data):
            barcode_fields = self.parse_ecia_barcode2d(barcode_split)
        else:
            return None

        sku = barcode_fields.get("supplier_part_number")
        if not (supplier_part := self.get_supplier_part(sku)):
            return None

        if po_number := barcode_fields.get("purchase_order_number"):
            barcode_fields["purchase_order_number"] = po_number.split("/")[0]

        return supplier_part, barcode_fields


TME_IS_QRCODE_REGEX = re.compile(r"([^\s:]+:[^\s:]+\s+)+PN:[^\s:]+\s+(\S+(\s|$)+)+")
TME_PARSE_QRCODE_REGEX = re.compile(r"([^\s:]+):([^\s:]+)(?:\s+|$)")
TME_PARSE_BARCODE2D_REGEX = re.compile(r"([^\s]+)(?:\s+|$)")
QRCODE_FIELD_NAME_MAP = {
    "PN": "supplier_part_number",
    "PO": "purchase_order_number",
    "MPN": "manufacturer_part_number",
    "QTY": "quantity",
}
