"""The MouserPlugin is meant to integrate the Mouser API into Inventree.

This plugin currently only match Mouser barcodes to supplier parts.
"""

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, SupplierBarcodeMixin


class MouserPlugin(SupplierBarcodeMixin, SettingsMixin, InvenTreePlugin):
    """Plugin to integrate the Mouser API into Inventree."""

    NAME = 'MouserPlugin'
    TITLE = _('Supplier Integration - Mouser')
    DESCRIPTION = _('Provides support for scanning Mouser barcodes')
    VERSION = '1.0.0'
    AUTHOR = _('InvenTree contributors')

    DEFAULT_SUPPLIER_NAME = 'Mouser'
    SETTINGS = {
        'SUPPLIER_ID': {
            'name': _('Supplier'),
            'description': _("The Supplier which acts as 'Mouser'"),
            'model': 'company.company',
        }
    }

    def extract_barcode_fields(self, barcode_data: str) -> dict[str, str]:
        """Get supplier_part and barcode_fields from Mouser DataMatrix-Code."""

        return self.parse_ecia_barcode2d(barcode_data)
