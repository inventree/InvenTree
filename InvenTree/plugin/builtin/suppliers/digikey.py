"""The DigiKeyPlugin is meant to integrate the DigiKey API into Inventree.

This plugin can currently only match DigiKey barcodes to supplier parts.
"""

import logging

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, SupplierBarcodeMixin

logger = logging.getLogger('inventree')


class DigiKeyPlugin(SupplierBarcodeMixin, SettingsMixin, InvenTreePlugin):
    """Plugin to integrate the DigiKey API into Inventree."""

    NAME = "DigiKeyPlugin"
    TITLE = _("Supplier Integration - DigiKey")
    DESCRIPTION = _("Provides support for scanning DigiKey barcodes")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    DEFAULT_SUPPLIER_NAME = "DigiKey"
    SETTINGS = {
        "SUPPLIER_ID": {
            "name": _("Supplier"),
            "description": _("The Supplier which acts as 'DigiKey'"),
            "model": "company.company",
        }
    }

    # Custom field identifiers for DigiKey
    SUPPLIER_PART_NUMBER = "30P"
