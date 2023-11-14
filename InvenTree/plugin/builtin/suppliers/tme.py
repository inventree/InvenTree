"""The TMEPlugin is meant to integrate the TME API into Inventree.

This plugin can currently only match TME barcodes to supplier parts.
"""

import logging
import re

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, SupplierBarcodeMixin

logger = logging.getLogger('inventree')


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

    # Custom field identifiers for TME
    SUPPLIER_PART_NUMBER = "PN:"
    MANUFACTURER_PART_NUMBER = "MPN:"
    CUSTOMER_ORDER_NUMBER = "CPO:"
    SUPPLIER_ORDER_NUMBER = "PO:"
    QUANTITY = "QTY:"

    TME_IS_QRCODE_REGEX = re.compile(r"([^\s:]+:[^\s:]+\s+)+(\S+(\s|$)+)+")
    TME_PARSE_QRCODE_REGEX = re.compile(r"([^\s:]+):([^\s:]+)(?:\s+|$)")
    TME_IS_BARCODE2D_REGEX = re.compile(r"(([^\s]+)(\s+|$))+")
    TME_PARSE_BARCODE2D_REGEX = re.compile(r"([^\s]+)(?:\s+|$)")

    @property
    def customer_order_number(self):
        """Extract customer order number"""
        order = super().customer_order_number

        if order:
            return order.split("/")[0]

    def parse_supplier_barcode_data(self, barcode_data):
        """Get supplier_part and barcode_fields from TME QR-Code or DataMatrix-Code."""

        if not isinstance(barcode_data, str):
            return None

        if self.TME_IS_QRCODE_REGEX.fullmatch(barcode_data):
            return str(barcode_data).strip().split(' ')
        elif self.TME_IS_BARCODE2D_REGEX.fullmatch(barcode_data):
            # TODO: Fix this one
            return None
        else:
            return None
