# -*- coding: utf-8 -*-

import plugins.plugin as plugin


class BarcodePlugin(plugin.InvenTreePlugin):
    """
    The BarcodePlugin class is the base class for any barcode plugin.
    """

    def __init__(self, barcode_data):
        plugin.InvenTreePlugin.__init__(self)

        self.data = barcode_data

    def hash(self):
        """
        Calculate a hash for the barcode data.
        This is supposed to uniquely identify the barcode contents,
        at least within the bardcode sub-type.
        """

        return ""

    def validate(self):
        """
        Default implementation returns False
        """
        return False

    def decode(self):
        """
        Decode the barcode, and craft a response
        """

        return None

    def render_part(self, part):
        return {
            'id': part.id,
            'name': part.full_name,
        }

    def render_stock_location(self, loc):
        return {
            "id": loc.id
        }

    def render_stock_item(self, item):

        return {
            "id": item.id,
        }
