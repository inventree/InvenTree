"""The MouserBarcodePlugin matches Mouser barcodes to supplier parts."""

import logging

from django.utils.translation import gettext_lazy as _

from company.models import ManufacturerPart, SupplierPart
from plugin import InvenTreePlugin
from plugin.mixins import BarcodeMixin

logger = logging.getLogger('inventree')


class MouserBarcodePlugin(BarcodeMixin, InvenTreePlugin):
    """BarcodePlugin for matching Mouser barcodes."""

    NAME = "MouserBarcode"
    TITLE = _("Mouser Barcodes")
    DESCRIPTION = _("Provides support for scanning Mouser barcodes")
    VERSION = "0.1.0"
    AUTHOR = _("InvenTree contributors")

    def scan(self, barcode_data):
        """Process a barcode to determine if it is a Mouser barcode."""
        MOUSER_MAGIC = ">[)>06"

        if not barcode_data.startswith(MOUSER_MAGIC):
            return

        barcode_data_entries = barcode_data.split("\x1d")[1:]
        barcode_fields = {}
        for entry in barcode_data_entries:
            if entry.startswith("K"):
                barcode_fields["order_number"] = entry[1:]
            elif entry.startswith("14K"):
                barcode_fields["line_item"] = entry[3:]
            elif entry.startswith("1P"):
                barcode_fields["mpn"] = entry[2:]
            elif entry.startswith("Q"):
                barcode_fields["quantity"] = entry[1:]
            elif entry.startswith("11K"):
                barcode_fields["invoice_number"] = entry[3:]
            elif entry.startswith("4L"):
                barcode_fields["country_of_origin"] = entry[2:]
            elif entry.startswith("1V"):
                barcode_fields["manufacturer"] = entry[2:]

        manufacturer_parts = ManufacturerPart.objects.filter(
            MPN__iexact=barcode_fields.get("mpn"))
        if not manufacturer_parts or len(manufacturer_parts) > 1:
            logger.warning(f"Found {len(manufacturer_parts)} manufacturer parts for MPN {barcode_fields.get('mpn')} with MouserBarcodePlugin plugin")
            return
        manufacturer_part = manufacturer_parts[0]

        supplier_parts = SupplierPart.objects.filter(
            manufacturer_part=manufacturer_part.pk)
        for supplier_part in supplier_parts:
            if "mouser" in supplier_part.supplier.name.lower():
                break
        else:
            return

        response = {
            SupplierPart.barcode_model_type(): {
                "pk": supplier_part.pk,
                "api_url": f"{SupplierPart.get_api_url()}{supplier_part.pk}/",
                "web_url": supplier_part.get_absolute_url(),
            }
        }

        return response
