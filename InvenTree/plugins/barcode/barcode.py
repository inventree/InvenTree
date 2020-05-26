# -*- coding: utf-8 -*-

import hashlib

from stock.serializers import StockItemSerializer, LocationSerializer
from part.serializers import PartSerializer

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

        The default implementation simply returns an MD5 hash of the barcode data,
        encoded to a string.

        This may be sufficient for most applications, but can obviously be overridden
        by a subclass.

        """

        hash = hashlib.md5(str(self.data).encode())
        return str(hash.hexdigest())

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
        """
        Render a Part object to JSON
        Use the existing serializer to do this.
        """

        serializer = PartSerializer(part)

        return serializer.data

    def render_stock_location(self, loc):
        """
        Render a StockLocation object to JSON
        Use the existing serializer to do this.
        """

        serializer = LocationSerializer(loc)

        return serializer.data

    def render_stock_item(self, item):
        """
        Render a StockItem object to JSON.
        Use the existing serializer to do this
        """

        serializer = StockItemSerializer(item, part_detail=True, location_detail=True, supplier_part_detail=True)

        return serializer.data
