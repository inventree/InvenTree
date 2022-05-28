
from django.urls import path, re_path, reverse
from django.utils.translation import gettext_lazy as _

from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from plugin import registry
from plugin.base.barcodes.mixins import hash_barcode
from plugin.builtin.barcodes.inventree_barcode import InvenTreeBarcodePlugin
from stock.models import StockItem
from stock.serializers import StockItemSerializer


class BarcodeScan(APIView):
    """Endpoint for handling generic barcode scan requests.

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
        """Respond to a barcode POST request."""
        data = request.data

        if 'barcode' not in data:
            raise ValidationError({'barcode': _('Must provide barcode_data parameter')})

        plugins = registry.with_mixin('barcode')

        barcode_data = data.get('barcode')

        # Ensure that the default barcode handler is installed
        plugins.append(InvenTreeBarcodePlugin())

        # Look for a barcode plugin which knows how to deal with this barcode
        plugin = None

        for current_plugin in plugins:
            current_plugin.init(barcode_data)

            if current_plugin.validate():
                plugin = current_plugin
                break

        match_found = False
        response = {}

        response['barcode_data'] = barcode_data

        # A plugin has been found!
        if plugin is not None:

            # Try to associate with a stock item
            item = plugin.getStockItem()

            if item is None:
                item = plugin.getStockItemByHash()

            if item is not None:
                response['stockitem'] = plugin.renderStockItem(item)
                response['url'] = reverse('stock-item-detail', kwargs={'pk': item.id})
                match_found = True

            # Try to associate with a stock location
            loc = plugin.getStockLocation()

            if loc is not None:
                response['stocklocation'] = plugin.renderStockLocation(loc)
                response['url'] = reverse('stock-location-detail', kwargs={'pk': loc.id})
                match_found = True

            # Try to associate with a part
            part = plugin.getPart()

            if part is not None:
                response['part'] = plugin.renderPart(part)
                response['url'] = reverse('part-detail', kwargs={'pk': part.id})
                match_found = True

            response['hash'] = plugin.hash()
            response['plugin'] = plugin.name

        # No plugin is found!
        # However, the hash of the barcode may still be associated with a StockItem!
        else:
            result_hash = hash_barcode(barcode_data)

            response['hash'] = result_hash
            response['plugin'] = None

            # Try to look for a matching StockItem
            try:
                item = StockItem.objects.get(uid=result_hash)
                serializer = StockItemSerializer(item, part_detail=True, location_detail=True, supplier_part_detail=True)
                response['stockitem'] = serializer.data
                response['url'] = reverse('stock-item-detail', kwargs={'pk': item.id})
                match_found = True
            except StockItem.DoesNotExist:
                pass

        if not match_found:
            response['error'] = _('No match found for barcode data')
        else:
            response['success'] = _('Match found for barcode data')

        return Response(response)


class BarcodeAssign(APIView):
    """Endpoint for assigning a barcode to a stock item.

    - This only works if the barcode is not already associated with an object in the database
    - If the barcode does not match an object, then the barcode hash is assigned to the StockItem
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request, *args, **kwargs):

        data = request.data

        if 'barcode' not in data:
            raise ValidationError({'barcode': _('Must provide barcode_data parameter')})

        if 'stockitem' not in data:
            raise ValidationError({'stockitem': _('Must provide stockitem parameter')})

        barcode_data = data['barcode']

        try:
            item = StockItem.objects.get(pk=data['stockitem'])
        except (ValueError, StockItem.DoesNotExist):
            raise ValidationError({'stockitem': _('No matching stock item found')})

        plugins = registry.with_mixin('barcode')

        plugin = None

        for current_plugin in plugins:
            current_plugin.init(barcode_data)

            if current_plugin.validate():
                plugin = current_plugin
                break

        match_found = False

        response = {}

        response['barcode_data'] = barcode_data

        # Matching plugin was found
        if plugin is not None:

            result_hash = plugin.hash()
            response['hash'] = result_hash
            response['plugin'] = plugin.name

            # Ensure that the barcode does not already match a database entry

            if plugin.getStockItem() is not None:
                match_found = True
                response['error'] = _('Barcode already matches Stock Item')

            if plugin.getStockLocation() is not None:
                match_found = True
                response['error'] = _('Barcode already matches Stock Location')

            if plugin.getPart() is not None:
                match_found = True
                response['error'] = _('Barcode already matches Part')

            if not match_found:
                item = plugin.getStockItemByHash()

                if item is not None:
                    response['error'] = _('Barcode hash already matches Stock Item')
                    match_found = True

        else:
            result_hash = hash_barcode(barcode_data)

            response['hash'] = result_hash
            response['plugin'] = None

            # Lookup stock item by hash
            try:
                item = StockItem.objects.get(uid=result_hash)
                response['error'] = _('Barcode hash already matches Stock Item')
                match_found = True
            except StockItem.DoesNotExist:
                pass

        if not match_found:
            response['success'] = _('Barcode associated with Stock Item')

            # Save the barcode hash
            item.uid = response['hash']
            item.save()

            serializer = StockItemSerializer(item, part_detail=True, location_detail=True, supplier_part_detail=True)
            response['stockitem'] = serializer.data

        return Response(response)


barcode_api_urls = [
    # Link a barcode to a part
    path('link/', BarcodeAssign.as_view(), name='api-barcode-link'),

    # Catch-all performs barcode 'scan'
    re_path(r'^.*$', BarcodeScan.as_view(), name='api-barcode-scan'),
]
