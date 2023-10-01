"""The DigiKeyPlugin is meant to integrate the DigiKey API into Inventree.

This plugin can currently only match DigiKey barcodes to supplier parts.
"""

import logging

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import SupplierBarcodeMixin

logger = logging.getLogger('inventree')


class DigiKeyPlugin(SupplierBarcodeMixin, InvenTreePlugin):
    """Plugin to integrate the DigiKey API into Inventree."""

    NAME = "DigiKeyPlugin"
    TITLE = _("Supplier Integration - DigiKey")
    DESCRIPTION = _("Provides support for scanning DigiKey barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    def parse_supplier_barcode_data(self, barcode_data):
        """Get supplier_part and barcode_fields from DigiKey DataMatrix-Code."""

        if not isinstance(barcode_data, str):
            return None

        if not (barcode_fields := self.parse_ecia_barcode2d(barcode_data)):
            return None

        sku = barcode_fields.get("supplier_part_number")
        if not (supplier_part := self.get_supplier_part(sku)):
            return None

        return supplier_part, barcode_fields
