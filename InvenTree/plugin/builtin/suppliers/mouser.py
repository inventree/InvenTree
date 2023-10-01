"""The MouserPlugin is meant to integrate the Mouser API into Inventree.

This plugin currently only match Mouser barcodes to supplier parts.
"""

import logging

from django.utils.translation import gettext_lazy as _

from company.models import Company
from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, SupplierBarcodeMixin

logger = logging.getLogger('inventree')


class MouserPlugin(SupplierBarcodeMixin, SettingsMixin, InvenTreePlugin):
    """Plugin to integrate the Mouser API into Inventree."""

    NAME = "MouserPlugin"
    TITLE = _("Supplier Integration - Mouser")
    DESCRIPTION = _("Provides support for scanning Mouser barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    SETTINGS = {
        "MOUSER_SUPPLIER": {
            "name": _("Mouser Supplier"),
            "description": _("The Supplier which acts as 'Mouser'"),
            "model": "company.company",
        }
    }

    def get_mouser_supplier(self):
        """Get the MOUSER_SUPPLIER supplier set in the plugin settings.

        If it's not defined, try to guess it and set it if possible.
        """
        if (mouser_pk := self.get_setting("MOUSER_SUPPLIER")):
            if not (mouser := Company.objects.get(pk=mouser_pk)):
                logger.error(
                    "No company with pk %d (set \"MOUSER_SUPPLIER\" pk to a valid value)",
                    mouser_pk
                )
                return None
        else:
            suppliers = Company.objects.filter(
                name__icontains="mouser", is_supplier=True)
            if len(suppliers) != 1:
                return None
            mouser = suppliers[0]
            self.set_setting("MOUSER_SUPPLIER", mouser.pk)

        return mouser

    def parse_supplier_barcode_data(self, barcode_data):
        """Get supplier_part and barcode_fields from Mouser DataMatrix-Code."""

        if not isinstance(barcode_data, str):
            return None

        if not (mouser := self.get_mouser_supplier()):
            return None

        if not (barcode_fields := self.parse_ecia_barcode2d(barcode_data)):
            return None

        sku = barcode_fields.get("supplier_part_number")
        mpn = barcode_fields.get("manufacturer_part_number")
        if not (supplier_part := self.get_supplier_part(sku, mouser, mpn)):
            return None

        return supplier_part, barcode_fields
