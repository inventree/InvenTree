"""
Main JSON interface views
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from django.http import JsonResponse

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .views import AjaxView
from .version import inventreeVersion, inventreeInstanceName

from plugins import plugins as inventree_plugins

# Load barcode plugins
print("INFO: Loading plugins")

barcode_plugins = inventree_plugins.load_barcode_plugins()
action_plugins = inventree_plugins.load_action_plugins()


class InfoView(AjaxView):
    """ Simple JSON endpoint for InvenTree information.
    Use to confirm that the server is running, etc.
    """

    def get(self, request, *args, **kwargs):

        data = {
            'server': 'InvenTree',
            'version': inventreeVersion(),
            'instance': inventreeInstanceName(),
        }

        return JsonResponse(data)


class ActionPluginView(APIView):
    """
    Endpoint for running custom action plugins.
    """

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):

        action = request.data.get('action', None)

        data = request.data.get('data', None)

        if action is None:
            return Response({
                'error': _("No action specified")
            })

        for plugin_class in action_plugins:
            if plugin_class.action_name() == action:

                plugin = plugin_class(request.user, data=data)

                plugin.perform_action()

                return Response(plugin.get_response())

        # If we got to here, no matching action was found
        return Response({
            'error': _("No matching action found for"),
            "action": action,
        })


class BarcodePluginView(APIView):
    """
    Endpoint for handling barcode scan requests.

    Barcode data are decoded by the client application,
    and sent to this endpoint (as a JSON object) for validation.

    A barcode could follow the internal InvenTree barcode format,
    or it could match to a third-party barcode format (e.g. Digikey).

    """

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):

        response = {}

        barcode_data = request.data.get('barcode', None)

        print("Barcode data:")
        print(barcode_data)

        if barcode_data is None:
            response['error'] = _('No barcode data provided')
        else:
            # Look for a barcode plugin that knows how to handle the data
            for plugin_class in barcode_plugins:

                # Instantiate the plugin with the provided plugin data
                plugin = plugin_class(barcode_data)

                if plugin.validate():
                    
                    # Plugin should return a dict response
                    response = plugin.decode()
                    
                    if type(response) is dict:
                        if 'success' not in response.keys() and 'error' not in response.keys():
                            response['success'] = _('Barcode successfully decoded')
                    else:
                        response = {
                            'error': _('Barcode plugin returned incorrect response')
                        }

                    response['plugin'] = plugin.plugin_name()
                    response['hash'] = plugin.hash()

                    break

        if 'error' not in response and 'success' not in response:
            response = {
                'error': _('Unknown barcode format'),
            }

        # Include the original barcode data
        response['barcode_data'] = barcode_data

        return Response(response)
