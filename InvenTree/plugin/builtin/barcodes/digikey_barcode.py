"""The DigiKeyBarcodePlugin matches DigiKey barcodes to supplier parts."""

from django.utils.translation import gettext_lazy as _

from company.models import SupplierPart
from plugin import InvenTreePlugin
from plugin.mixins import BarcodeMixin


class DigiKeyBarcodePlugin(BarcodeMixin, InvenTreePlugin):
    """BarcodePlugin for matching DigiKey barcodes."""

    NAME = "DigiKeyBarcode"
    TITLE = _("DigiKey Barcodes")
    DESCRIPTION = _("Provides support for scanning DigiKey barcodes")
    VERSION = "0.1.0"
    AUTHOR = _("InvenTree contributors")

    def scan(self, barcode_data):
        DIGIKEY_MAGIC = "[)>\x1e06"

        if not barcode_data.startswith(DIGIKEY_MAGIC):
            return

        barcode_data_entries = barcode_data.strip("0").split("\x1d")[1:]
        barcode_fields = {}
        for entry in barcode_data_entries:
            if entry.startswith("P"):
                barcode_fields["sku"] = entry[1:]
            elif entry.startswith("1P"):
                barcode_fields["mpn"] = entry[2:]
            elif entry.startswith("1K"):
                barcode_fields["order_number"] = entry[2:]
            elif entry.startswith("10K"):
                barcode_fields["invoice_number"] = entry[3:]
            elif entry.startswith("11K"):
                pass
            elif entry.startswith("Q"):
                barcode_fields["quantity"] = entry[1:]
            elif entry.startswith("11Z"):
                pass
            elif entry.startswith("12Z"):
                barcode_fields["part_id"] = entry[3:]
            elif entry.startswith("13Z"):
                barcode_fields["load_id"] = entry[3:]

        supplier_parts = SupplierPart.objects.filter(SKU__iexact=barcode_fields.get("sku"))
        if not supplier_parts or len(supplier_parts) > 1:
            return
        supplier_part = supplier_parts[0]

        response = {
            SupplierPart.barcode_model_type(): {
                "pk": supplier_part.pk,
                "api_url": f"{SupplierPart.get_api_url()}{supplier_part.pk}/",
                "web_url": supplier_part.get_absolute_url(),
            }
        }

        return response
