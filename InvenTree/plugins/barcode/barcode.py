# -*- coding: utf-8 -*-

import plugins.plugin as plugin


class BarcodePlugin(plugin.InvenTreePlugin):
    """
    The BarcodePlugin class is the base class for any barcode plugin.
    """

    def validate_barcode(self, barcode_data):
        """
        Default implementation returns False
        """
        return False

    def decode_barcode(self, barcode_data):
        """
        Decode the barcode, and craft a response
        """

        return None

    def __init__(self):
        plugin.InvenTreePlugin.__init__(self)
