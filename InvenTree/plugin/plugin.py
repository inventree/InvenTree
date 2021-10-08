# -*- coding: utf-8 -*-
"""Base Class for InvenTree plugins"""


class InvenTreePlugin():
    """
    Base class for a plugin
    """

    # Override the plugin name for each concrete plugin instance
    PLUGIN_NAME = ''

    def plugin_name(self):
        """get plugin name"""
        return self.PLUGIN_NAME

    def __init__(self):
        pass
