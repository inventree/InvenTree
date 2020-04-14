# -*- coding: utf-8 -*-


class InvenTreePlugin():
    """
    Base class for a Barcode plugin
    """

    # Override the plugin name for each concrete plugin instance
    PLUGIN_NAME = ''

    def get_name(self):
        return self.PLUGIN_NAME

    def __init__(self):
        pass
