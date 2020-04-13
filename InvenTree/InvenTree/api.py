"""
Main JSON interface views
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import JsonResponse

from .views import AjaxView
from .version import inventreeVersion, inventreeInstanceName


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


class BarcodeScanView(AjaxView):
    """
    Endpoint for handling barcode scan requests.
    """

    def get(self, request, *args, **kwargs):
        
        data = {
            'barcode': 'Hello world',
        }

        return JsonResponse(data)
