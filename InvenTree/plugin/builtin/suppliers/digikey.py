"""The DigiKeyPlugin is meant to integrate the DigiKey API into Inventree.

This plugin can currently only match DigiKey barcodes to supplier parts.
"""

import logging

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.base.barcodes.mixins import SupplierBarcodeData
from plugin.mixins import SettingsMixin, SupplierBarcodeMixin

logger = logging.getLogger('inventree')


class DigiKeyPlugin(SupplierBarcodeMixin, SettingsMixin, InvenTreePlugin):
    """Plugin to integrate the DigiKey API into Inventree."""

    NAME = "DigiKeyPlugin"
    TITLE = _("Supplier Integration - DigiKey")
    DESCRIPTION = _("Provides support for scanning DigiKey barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    DEFAULT_SUPPLIER_NAME = "DigiKey"
    SETTINGS = {
        "SUPPLIER_ID": {
            "name": _("Supplier"),
            "description": _("The Supplier which acts as 'DigiKey'"),
            "model": "company.company",
        }
    }

    def parse_supplier_barcode_data(self, barcode_data):
        """Get supplier_part and barcode_fields from DigiKey DataMatrix-Code."""

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
