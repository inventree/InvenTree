"""The LCSCPlugin is meant to integrate the LCSC API into Inventree.

This plugin can currently only match LCSC barcodes to supplier parts.
"""

import logging
import re

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, SupplierBarcodeMixin

logger = logging.getLogger('inventree')


class LCSCPlugin(SupplierBarcodeMixin, SettingsMixin, InvenTreePlugin):
    """Plugin to integrate the LCSC API into Inventree."""

    NAME = "LCSCPlugin"
    TITLE = _("Supplier Integration - LCSC")
    DESCRIPTION = _("Provides support for scanning LCSC barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    DEFAULT_SUPPLIER_NAME = "LCSC"
    SETTINGS = {
        "SUPPLIER_ID": {
            "name": _("Supplier"),
            "description": _("The Supplier which acts as 'LCSC'"),
            "model": "company.company",
        }
    }

    # Custom field identifiers for LCSC
    SUPPLIER_PART_NUMBER = "pc:"
    MANUFACTURER_PART_NUMBER = "pm:"
    QUANTITY = "qty:"
    CUSTOMER_ORDER_NUMBER = "on:"

    LCSC_BARCODE_REGEX = re.compile(r"^{((?:[^:,]+:[^:,]*,)*(?:[^:,]+:[^:,]*))}$")

    def parse_supplier_barcode_data(self, barcode_data):
        """Get supplier_part and barcode_fields from LCSC QR-Code."""

        if not isinstance(barcode_data, str):
            return None

        if not (match := self.LCSC_BARCODE_REGEX.fullmatch(barcode_data)):
            return None

        return match.group(1).split(',')
