# -*- coding: utf-8 -*-

from . import barcode


class InvenTreeBarcodePlugin(barcode.BarcodePlugin):

    PLUGIN_NAME = "InvenTreeBarcodePlugin"

    def validate_barcode(self, barcode_data):
        """
        An "InvenTree" barcode must include the following tags:

        {
            'tool': 'InvenTree',
            'version': <anything>
        }

        """

        for key in ['tool', 'version']:
            if key not in barcode_data.keys():
                return False

        if not barcode_data['tool'] == 'InvenTree':
            return False

        return True

    def decode_barcode(self, barcode_data):
        pass
