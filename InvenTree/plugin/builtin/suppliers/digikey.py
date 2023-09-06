"""The DigiKeyPlugin is meant to integrate the DigiKey API into Inventree.
It can currently only match DigiKey barcodes to supplier parts."""

import logging

from django.utils.translation import gettext_lazy as _

from company.models import SupplierPart
from plugin import InvenTreePlugin
from plugin.mixins import BarcodeMixin
from .supplier_barcodes import get_order_data, get_supplier_part, parse_ecia_barcode2d

logger = logging.getLogger('inventree')


class DigiKeyPlugin(BarcodeMixin, InvenTreePlugin):
    """Plugin to integrate the DigiKey API into Inventree."""

    NAME = "DigiKeyPlugin"
    TITLE = _("Supplier Integration - DigiKey")
    DESCRIPTION = _("Provides support for scanning DigiKey barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    def scan(self, barcode_data):
        """Process a barcode to determine if it is a DigiKey barcode."""

        if not (barcode_fields := parse_ecia_barcode2d(barcode_data)):
            return

        sku = barcode_fields.get("supplier_part_number")
        if not (supplier_part := get_supplier_part(sku)):
            return None

        data = {
            "pk": supplier_part.pk,
            "api_url": f"{SupplierPart.get_api_url()}{supplier_part.pk}/",
            "web_url": supplier_part.get_absolute_url(),
        }

        data.update(get_order_data(barcode_fields))

        return {SupplierPart.barcode_model_type(): data}
