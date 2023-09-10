"""The LCSCPlugin is meant to integrate the LCSC API into Inventree.

This plugin can currently only match LCSC barcodes to supplier parts.
"""

import logging
import re

from django.utils.translation import gettext_lazy as _

from company.models import SupplierPart
from plugin import InvenTreePlugin
from plugin.mixins import BarcodeMixin

logger = logging.getLogger('inventree')


class LCSCPlugin(BarcodeMixin, InvenTreePlugin):
    """Plugin to integrate the LCSC API into Inventree."""

    NAME = "LCSCPlugin"
    TITLE = _("Supplier Integration - LCSC")
    DESCRIPTION = _("Provides support for scanning LCSC barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    def scan(self, barcode_data):
        """Process a barcode to determine if it is a LCSC barcode."""

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

        data = {
            "pk": supplier_part.pk,
            "api_url": f"{SupplierPart.get_api_url()}{supplier_part.pk}/",
            "web_url": supplier_part.get_absolute_url(),
        }

        return {SupplierPart.barcode_model_type(): data}


LCSC_BARCODE_REGEX = re.compile(r"^{((?:[^:,]+:[^:,]*,)*(?:[^:,]+:[^:,]*))}$")
BARCODE_FIELD_NAME_MAP = {
    "pc": "supplier_part_number",
    "on": "purchase_order_number",
    "pm": "manufacturer_part_number",
    "qty": "quantity",
}
