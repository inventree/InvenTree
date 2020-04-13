"""
Main JSON interface views
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from .views import AjaxView
from .version import inventreeVersion, inventreeInstanceName

from plugins import plugins as inventree_plugins


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


class BarcodeScanView(APIView):
    """
    Endpoint for handling barcode scan requests.

    Barcode data are decoded by the client application,
    and sent to this endpoint (as a JSON object) for validation.

    A barcode could follow the internal InvenTree barcode format,
    or it could match to a third-party barcode format (e.g. Digikey).

    """

    def post(self, request, *args, **kwargs):

        data = {
            'barcode': 'Hello world',
        }

        plugins = inventree_plugins.load_barcode_plugins()

        for plugin in plugins:
            print("Testing plugin:", plugin.PLUGIN_NAME)
            if plugin().validate_barcode(request.data):
                print("success!")

        return Response({
            'success': 'OK',
            'data': data,
            'post': request.data,
        })
