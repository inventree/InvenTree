"""
Main JSON interface views
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.utils.translation import ugettext_lazy as _
from django.http import JsonResponse

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .views import AjaxView
from .version import inventreeVersion, inventreeApiVersion, inventreeInstanceName
from .status import is_worker_running
from .helpers import str2bool

from plugins import plugins as inventree_plugins

from company.models import Company
from company.serializers import CompanySerializer
from stock.models import StockLocation, StockItem
from stock.serializers import LocationSerializer, StockItemSerializer
from order.models import PurchaseOrder
from order.serializers import POSerializer

logger = logging.getLogger("inventree")


logger.info("Loading action plugins...")
action_plugins = inventree_plugins.load_action_plugins()


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

        for plugin_class in action_plugins:
            if plugin_class.action_name() == action:

                plugin = plugin_class(request.user, data=data)

                plugin.perform_action()

                return Response(plugin.get_response())

        # If we got to here, no matching action was found
        return Response({
            'error': _("No matching action found"),
            "action": action,
        })


class TrackingMixin:
    """ Mixin for Tracking entrie Views """

    def get_serializer(self, *args, **kwargs):
        try:
            kwargs['item_detail'] = str2bool(self.request.query_params.get('item_detail', False))
        except:
            pass

        try:
            kwargs['user_detail'] = str2bool(self.request.query_params.get('user_detail', False))
        except:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)

        data = serializer.data

        # Attempt to add extra context information to the historical data
        for item in data:
            deltas = item['deltas']

            if not deltas:
                deltas = {}

            # Add location detail
            if 'location' in deltas:
                try:
                    location = StockLocation.objects.get(pk=deltas['location'])
                    serializer = LocationSerializer(location)
                    deltas['location_detail'] = serializer.data
                except:
                    pass

            # Add stockitem detail
            if 'stockitem' in deltas:
                try:
                    stockitem = StockItem.objects.get(pk=deltas['stockitem'])
                    serializer = StockItemSerializer(stockitem)
                    deltas['stockitem_detail'] = serializer.data
                except:
                    pass

            # Add customer detail
            if 'customer' in deltas:
                try:
                    customer = Company.objects.get(pk=deltas['customer'])
                    serializer = CompanySerializer(customer)
                    deltas['customer_detail'] = serializer.data
                except:
                    pass

            # Add purchaseorder detail
            if 'purchaseorder' in deltas:
                try:
                    order = PurchaseOrder.objects.get(pk=deltas['purchaseorder'])
                    serializer = POSerializer(order)
                    deltas['purchaseorder_detail'] = serializer.data
                except:
                    pass

        if request.is_ajax():
            return JsonResponse(data, safe=False)
        else:
            return Response(data)

    def create(self, request, *args, **kwargs):
        """ Create a new Tracking object

        Here we override the default 'create' implementation,
        to save the user information associated with the request object.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Record the user who created this Part object
        item = serializer.save()
        item.user = request.user
        item.system = False

        # quantity field cannot be explicitly adjusted  here
        item.quantity = item.item.quantity
        item.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'item',
        'user',
    ]

    ordering = '-date'

    ordering_fields = [
        'date',
    ]

    search_fields = [
        'title',
        'notes',
    ]
