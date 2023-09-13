"""The DigiKeyPlugin is meant to integrate the DigiKey API into Inventree.

This plugin can currently only match DigiKey barcodes to supplier parts.
"""

import logging

from django.utils.translation import gettext_lazy as _

from company.models import SupplierPart
from plugin import InvenTreePlugin
from plugin.mixins import BarcodeMixin

logger = logging.getLogger('inventree')


class DigiKeyPlugin(BarcodeMixin, InvenTreePlugin):
    """Plugin to integrate the DigiKey API into Inventree."""

    NAME = "DigiKeyPlugin"
    TITLE = _("Supplier Integration - DigiKey")
    DESCRIPTION = _("Provides support for scanning DigiKey barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    def get_supplier_part(self, barcode_data):
        """Get supplier_part from barcode data"""

        if not isinstance(barcode_data, str):
            return None, None

        if not (barcode_fields := self.parse_ecia_barcode2d(barcode_data)):
            return None, None

        sku = barcode_fields.get("supplier_part_number")
        if not (supplier_part := self.get_supplier_part(sku)):
            return None, None

        return supplier_part, barcode_fields

    def scan(self, barcode_data):
        """Process a barcode to determine if it is a DigiKey barcode."""

        supplier_part, _ = self.get_supplier_part(barcode_data)
        if supplier_part is None:
            return None

        data = {
            "pk": supplier_part.pk,
            "api_url": f"{SupplierPart.get_api_url()}{supplier_part.pk}/",
            "web_url": supplier_part.get_absolute_url(),
        }

        return {SupplierPart.barcode_model_type(): data}

    def scan_receive_item(self, barcode_data, user, purchase_order=None, location=None):
        """Process a digikey barcode to receive an item from a placed purchase order."""

        supplier_part, barcode_fields = self.get_supplier_part(barcode_data)
        if supplier_part is None:
            return None

        return self.receive_purchase_order_item(
            supplier_part,
            user,
            quantity=barcode_fields.get("quantity"),
            order_number=barcode_fields.get("purchase_order_number"),
            purchase_order=purchase_order,
            location=location,
            barcode=barcode_data,
        )
