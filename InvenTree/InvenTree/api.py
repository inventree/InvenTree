"""
Main JSON interface views
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.http import JsonResponse

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from rest_framework import permissions
from rest_framework.exceptions import ParseError, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from InvenTree.tasks import offload_task

from .views import AjaxView
from .version import inventreeVersion, inventreeApiVersion, inventreeInstanceName
from .status import is_worker_running

from stock.models import StockItem, StockLocation

from plugin import registry


class InfoView(AjaxView):
    """ Simple JSON endpoint for InvenTree information.
    Use to confirm that the server is running, etc.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):

        data = {
            'server': 'InvenTree',
            'version': inventreeVersion(),
            'instance': inventreeInstanceName(),
            'apiVersion': inventreeApiVersion(),
            'worker_running': is_worker_running(),
            'plugins_enabled': settings.PLUGINS_ENABLED,
        }

        return JsonResponse(data)


class NotFoundView(AjaxView):
    """
    Simple JSON view when accessing an invalid API view.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):

        data = {
            'details': _('API endpoint not found'),
            'url': request.build_absolute_uri(),
        }

        return JsonResponse(data, status=404)


class APIDownloadMixin:
    """
    Mixin for enabling a LIST endpoint to be downloaded a file.

    To download the data, add the ?export=<fmt> to the query string.

    The implementing class must provided a download_queryset method,
    e.g.

    def download_queryset(self, queryset, export_format):
        dataset = StockItemResource().export(queryset=queryset)

        filedata = dataset.export(export_format)

        filename = 'InvenTree_Stocktake_{date}.{fmt}'.format(
            date=datetime.now().strftime("%d-%b-%Y"),
            fmt=export_format
        )

        return DownloadFile(filedata, filename)
    """

    def get(self, request, *args, **kwargs):

        export_format = request.query_params.get('export', None)

        if export_format and export_format in ['csv', 'tsv', 'xls', 'xlsx']:
            queryset = self.filter_queryset(self.get_queryset())
            return self.download_queryset(queryset, export_format)

        else:
            # Default to the parent class implementation
            return super().get(request, *args, **kwargs)

    def download_queryset(self, queryset, export_format):
        raise NotImplementedError("download_queryset method not implemented!")


class AttachmentMixin:
    """
    Mixin for creating attachment objects,
    and ensuring the user information is saved correctly.
    """

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]

    def perform_create(self, serializer):
        """ Save the user information when a file is uploaded """

        attachment = serializer.save()
        attachment.user = self.request.user
        attachment.save()


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

        action_plugins = registry.with_mixin('action')
        for plugin in action_plugins:
            if plugin.action_name() == action:
                # TODO @matmair use easier syntax once InvenTree 0.7.0 is released
                plugin.init(request.user, data=data)

                plugin.perform_action()

                return Response(plugin.get_response())

        # If we got to here, no matching action was found
        raise NotFound({
            'error': _("No matching action found"),
            "action": action,
        })


class LocatePluginView(APIView):
    """
    Endpoint for using a custom plugin to identify or 'locate' a stock item or location
    """

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

        if not item_pk and not location_pk:
            raise ParseError("Must supply either 'item' or 'location' parameter")

        data = {
            "success": "Identification plugin activated",
            "plugin": plugin,
        }

        # StockItem takes priority
        if item_pk:
            try:
                StockItem.objects.get(pk=item_pk)

                offload_task('plugin.registry.call_function', plugin, 'locate_stock_item', item_pk)

                data['item'] = item_pk

                return Response(data)

            except StockItem.DoesNotExist:
                raise NotFound("StockItem matching PK '{item}' not found")

        elif location_pk:
            try:
                StockLocation.objects.get(pk=location_pk)

                offload_task('plugin.registry.call_function', plugin, 'locate_stock_location', location_pk)

                data['location'] = location_pk

                return Response(data)

            except StockLocation.DoesNotExist:
                raise NotFound("StockLocation matching PK {'location'} not found")

        else:
            raise NotFound()
