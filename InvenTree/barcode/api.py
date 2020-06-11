# -*- coding: utf-8 -*-

import hashlib
from django.conf.urls import url

from rest_framework.exceptions import ValidationError

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

import InvenTree.plugins as InvenTreePlugins

from stock.models import StockItem
from stock.serializers import StockItemSerializer

import barcode.plugins as BarcodePlugins
from barcode.barcode import BarcodePlugin, load_barcode_plugins, hash_barcode


class BarcodeScan(APIView):
    """
    Endpoint for handling generic barcode scan requests.

    Barcode data are decoded by the client application,
    and sent to this endpoint (as a JSON object) for validation.

    A barcode could follow the internal InvenTree barcode format,
    or it could match to a third-party barcode format (e.g. Digikey).

    When a barcode is sent to the server, the following parameters must be provided:

    - barcode: The raw barcode data

    plugins:
    Third-party barcode formats may be supported using 'plugins'
    (more information to follow)

    hashing:
    Barcode hashes are calculated using MD5

    """

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):
        """
        Respond to a barcode POST request
        """

        data = request.data

        if 'barcode' not in data:
            raise ValidationError({'barcode': 'Must provide barcode_data parameter'})

        plugins = load_barcode_plugins()

        barcode_data = data.get('barcode')

        # Look for a barcode plugin which knows how to deal with this barcode
        plugin = None

        for plugin_class in plugins:
            plugin_instance = plugin_class(barcode_data)

            if plugin_instance.validate():
                plugin = plugin_instance
                break

        match_found = False
        response = {}

        response['barcode_data'] = barcode_data

        # A plugin has been found!
        if plugin is not None:
            
            # Try to associate with a stock item
            item = plugin.getStockItem()

            if item is not None:
                response['stockitem'] = plugin.renderStockItem(item)
                match_found = True

            # Try to associate with a stock location
            loc = plugin.getStockLocation()

            if loc is not None:
                response['stocklocation'] = plugin.renderStockLocation(loc)
                match_found = True

            # Try to associate with a part
            part = plugin.getPart()

            if part is not None:
                response['part'] = plugin.renderPart(part)
                match_found = True

            response['hash'] = plugin.hash()
            response['plugin'] = plugin.name

        # No plugin is found!
        # However, the hash of the barcode may still be associated with a StockItem!
        else:
            hash = hash_barcode(barcode_data)

            response['hash'] = hash
            response['plugin'] = None

            # Try to look for a matching StockItem
            try:
                item = StockItem.objects.get(uid=hash)
                serializer = StockItemSerializer(item, part_detail=True, location_detail=True, supplier_part_detail=True)
                response['stockitem'] = serializer.data
                match_found = True
            except StockItem.DoesNotExist:
                pass

        if not match_found:
            response['error'] = 'No match found for barcode data'
        else:
            response['success'] = 'Match found for barcode data'

        return Response(response)

barcode_api_urls = [
    
    # Catch-all performs barcode 'scan'
    url(r'^.*$', BarcodeScan.as_view(), name='api-barcode-plugin'),
]