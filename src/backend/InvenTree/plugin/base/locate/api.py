"""API for location plugins."""

from rest_framework import permissions, serializers
from rest_framework.exceptions import NotFound, ParseError, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from InvenTree.exceptions import log_error
from InvenTree.tasks import offload_task
from plugin.registry import call_plugin_function, registry
from stock.models import StockItem, StockLocation


class LocatePluginSerializer(serializers.Serializer):
    """Serializer for the LocatePluginView API endpoint."""

    plugin = serializers.CharField(
        help_text='Plugin to use for location identification'
    )
    item = serializers.IntegerField(required=False, help_text='StockItem to identify')
    location = serializers.IntegerField(
        required=False, help_text='StockLocation to identify'
    )


class LocatePluginView(GenericAPIView):
    """Endpoint for using a custom plugin to identify or 'locate' a stock item or location."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LocatePluginSerializer

    def post(self, request, *args, **kwargs):
        """Identify or 'locate' a stock item or location with a plugin."""
        # Check inputs and offload the task to the plugin
        # Which plugin to we wish to use?
        plugin = request.data.get('plugin', None)

        if not plugin:
            raise ParseError("'plugin' field must be supplied")

        # Check that the plugin exists, and supports the 'locate' mixin
        plugins = registry.with_mixin('locate')

        if plugin not in [p.slug for p in plugins]:
            raise ParseError(
                f"Plugin '{plugin}' is not installed, or does not support the location mixin"
            )

        # StockItem to identify
        item_pk = request.data.get('item', None)

        # StockLocation to identify
        location_pk = request.data.get('location', None)

        data = {'success': 'Identification plugin activated', 'plugin': plugin}

        # StockItem takes priority
        if item_pk:
            try:
                StockItem.objects.get(pk=item_pk)

                offload_task(
                    call_plugin_function,
                    plugin,
                    'locate_stock_item',
                    item_pk,
                    group='plugin',
                )

                data['item'] = item_pk

                return Response(data)

            except (ValueError, StockItem.DoesNotExist):
                raise NotFound(f"StockItem matching PK '{item_pk}' not found")
            except Exception:
                log_error('locate_stock_item')
                return ValidationError('Error locating stock item')

        elif location_pk:
            try:
                StockLocation.objects.get(pk=location_pk)

                offload_task(
                    call_plugin_function,
                    plugin,
                    'locate_stock_location',
                    location_pk,
                    group='plugin',
                )

                data['location'] = location_pk

                return Response(data)

            except (ValueError, StockLocation.DoesNotExist):
                raise NotFound(f"StockLocation matching PK '{location_pk}' not found")
            except Exception:
                log_error('locate_stock_location')
                return ValidationError('Error locating stock location')
        else:
            raise ParseError("Must supply either 'item' or 'location' parameter")
