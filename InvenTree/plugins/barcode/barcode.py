# -*- coding: utf-8 -*-


class BarcodePlugin:
    """
    The BarcodePlugin class is the base class for any barcode plugin.
    """

    # Override this for each actual plugin
    PLUGIN_NAME = ''

    def validate_barcode(self, barcode_data):
        """
        Default implementation returns False
        """
        return False

    def __init__(self):
        pass
