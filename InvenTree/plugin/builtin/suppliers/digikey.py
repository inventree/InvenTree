"""The DigiKeyPlugin is meant to integrate the DigiKey API into Inventree.

This plugin can currently only match DigiKey barcodes to supplier parts.
"""

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, SupplierBarcodeMixin


class DigiKeyPlugin(SupplierBarcodeMixin, SettingsMixin, InvenTreePlugin):
    """Plugin to integrate the DigiKey API into Inventree."""

    NAME = 'DigiKeyPlugin'
    TITLE = _('Supplier Integration - DigiKey')
    DESCRIPTION = _('Provides support for scanning DigiKey barcodes')
    VERSION = '1.0.0'
    AUTHOR = _('InvenTree contributors')

    DEFAULT_SUPPLIER_NAME = 'DigiKey'

    SETTINGS = {
        'SUPPLIER_ID': {
            'name': _('Supplier'),
            'description': _("The Supplier which acts as 'DigiKey'"),
            'model': 'company.company',
        }
    }

    def extract_barcode_fields(self, barcode_data) -> dict[str, str]:
        """Extract barcode fields from a DigiKey plugin."""
        return self.parse_ecia_barcode2d(barcode_data)
