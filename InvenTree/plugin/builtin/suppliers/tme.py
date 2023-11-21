"""The TMEPlugin is meant to integrate the TME API into Inventree.

This plugin can currently only match TME barcodes to supplier parts.
"""

import re

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, SupplierBarcodeMixin


class TMEPlugin(SupplierBarcodeMixin, SettingsMixin, InvenTreePlugin):
    """Plugin to integrate the TME API into Inventree."""

    NAME = "TMEPlugin"
    TITLE = _("Supplier Integration - TME")
    DESCRIPTION = _("Provides support for scanning TME barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    DEFAULT_SUPPLIER_NAME = "TME"
    SETTINGS = {
        "SUPPLIER_ID": {
            "name": _("Supplier"),
            "description": _("The Supplier which acts as 'TME'"),
            "model": "company.company",
        }
    }

    TME_IS_QRCODE_REGEX = re.compile(r"([^\s:]+:[^\s:]+\s+)+(\S+(\s|$)+)+")
    TME_IS_BARCODE2D_REGEX = re.compile(r"(([^\s]+)(\s+|$))+")

    # Custom field mapping
    TME_QRCODE_FIELDS = {
        "PN": SupplierBarcodeMixin.SUPPLIER_PART_NUMBER,
        "PO": SupplierBarcodeMixin.CUSTOMER_ORDER_NUMBER,
        "MPN": SupplierBarcodeMixin.MANUFACTURER_PART_NUMBER,
        "QTY": SupplierBarcodeMixin.QUANTITY,
    }

    def extract_barcode_fields(self, barcode_data: str) -> dict[str, str]:
        """Get supplier_part and barcode_fields from TME QR-Code or DataMatrix-Code."""

        barcode_fields = {}

        if self.TME_IS_QRCODE_REGEX.fullmatch(barcode_data):
            # Custom QR Code format e.g. "QTY: 1 PN:12345"
            for item in barcode_data.split(" "):
                if ":" in item:
                    key, value = item.split(":")
                    if key in self.TME_QRCODE_FIELDS:
                        barcode_fields[self.TME_QRCODE_FIELDS[key]] = value

            return barcode_fields

        elif self.TME_IS_BARCODE2D_REGEX.fullmatch(barcode_data):
            # 2D Barcode format e.g. "PWBP-302 1PMPNWBP-302 Q1 K19361337/1"
            for item in barcode_data.split(" "):
                for k, v in self.ecia_field_map().items():
                    if item.startswith(k):
                        barcode_fields[v] = item[len(k):]
        else:
            return {}

        # Custom handling for order number
        if SupplierBarcodeMixin.CUSTOMER_ORDER_NUMBER in barcode_fields:
            order_number = barcode_fields[SupplierBarcodeMixin.CUSTOMER_ORDER_NUMBER]
            order_number = order_number.split("/")[0]
            barcode_fields[SupplierBarcodeMixin.CUSTOMER_ORDER_NUMBER] = order_number

        return barcode_fields
