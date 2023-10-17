"""The MouserPlugin is meant to integrate the Mouser API into Inventree.

This plugin currently only match Mouser barcodes to supplier parts.
"""

import logging

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.base.barcodes.mixins import SupplierBarcodeData
from plugin.mixins import SettingsMixin, SupplierBarcodeMixin

logger = logging.getLogger('inventree')


class MouserPlugin(SupplierBarcodeMixin, SettingsMixin, InvenTreePlugin):
    """Plugin to integrate the Mouser API into Inventree."""

    NAME = "MouserPlugin"
    TITLE = _("Supplier Integration - Mouser")
    DESCRIPTION = _("Provides support for scanning Mouser barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    DEFAULT_SUPPLIER_NAME = "Mouser"
    SETTINGS = {
        "SUPPLIER_ID": {
            "name": _("Supplier"),
            "description": _("The Supplier which acts as 'Mouser'"),
            "model": "company.company",
        }
    }

    def parse_supplier_barcode_data(self, barcode_data):
        """Get supplier_part and barcode_fields from Mouser DataMatrix-Code."""

        if not isinstance(barcode_data, str):
            return None

        if not (barcode_fields := self.parse_ecia_barcode2d(barcode_data)):
            return None

        return SupplierBarcodeData(
            SKU=barcode_fields.get("supplier_part_number"),
            MPN=barcode_fields.get("manufacturer_part_number"),
            quantity=barcode_fields.get("quantity"),
            order_number=barcode_fields.get("purchase_order_number"),
        )
