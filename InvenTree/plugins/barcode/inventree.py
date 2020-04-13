# -*- coding: utf-8 -*-

from . import barcode


class InvenTreeBarcodePlugin(barcode.BarcodePlugin):

    PLUGIN_NAME = "InvenTreeBarcodePlugin"

    def validate_barcode(self, barcode_data):

        print("testing")

        return True
