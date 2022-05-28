"""API for location plugins"""

from rest_framework import permissions
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.response import Response
from rest_framework.views import APIView

from InvenTree.tasks import offload_task
from plugin.registry import registry
from stock.models import StockItem, StockLocation


class LocatePluginView(APIView):
    """Endpoint for using a custom plugin to identify or 'locate' a stock item or location"""

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):

        # Which plugin to we wish to use?
        plugin = request.data.get('plugin', None)

        if not plugin:
            raise ParseError("'plugin' field must be supplied")

        # Check that the plugin exists, and supports the 'locate' mixin
        plugins = registry.with_mixin('locate')

        if plugin not in [p.slug for p in plugins]:
            raise ParseError(f"Plugin '{plugin}' is not installed, or does not support the location mixin")

        # StockItem to identify
        item_pk = request.data.get('item', None)

        # StockLocation to identify
        location_pk = request.data.get('location', None)

        data = {
            "success": "Identification plugin activated",
            "plugin": plugin,
        }

        # StockItem takes priority
        if item_pk:
            try:
                StockItem.objects.get(pk=item_pk)

                offload_task(registry.call_plugin_function, plugin, 'locate_stock_item', item_pk)

                data['item'] = item_pk

                return Response(data)

            except (ValueError, StockItem.DoesNotExist):
                raise NotFound(f"StockItem matching PK '{item_pk}' not found")

        elif location_pk:
            try:
                StockLocation.objects.get(pk=location_pk)

                offload_task(registry.call_plugin_function, plugin, 'locate_stock_location', location_pk)

                data['location'] = location_pk

                return Response(data)

            except (ValueError, StockLocation.DoesNotExist):
                raise NotFound(f"StockLocation matching PK '{location_pk}' not found")

        else:
            raise ParseError("Must supply either 'item' or 'location' parameter")
