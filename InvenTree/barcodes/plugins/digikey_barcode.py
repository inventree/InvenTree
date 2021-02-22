# -*- coding: utf-8 -*-

"""
DigiKey barcode decoding
"""

from barcodes.barcode import BarcodePlugin


class DigikeyBarcodePlugin(BarcodePlugin):

    PLUGIN_NAME = "DigikeyBarcode"

    def validate(self):
        """
        TODO: Validation of Digikey barcodes.
        """

        return False
