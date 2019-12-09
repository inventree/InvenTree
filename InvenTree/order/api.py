"""
JSON API for the Order app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions
from rest_framework import filters
from rest_framework.response import Response

from django.conf import settings
from django.conf.urls import url

from InvenTree.status_codes import OrderStatus

import os

from part.models import Part

from .models import PurchaseOrder, PurchaseOrderLineItem
from .serializers import POSerializer, POLineItemSerializer


class POList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of Order objects

    - GET: Return list of PO objects (with filters)
    - POST: Create a new PurchaseOrder object
    """

    queryset = PurchaseOrder.objects.all()
    serializer_class = POSerializer

    def list(self, request, *args, **kwargs):

        queryset = self.get_queryset().prefetch_related('supplier', 'lines')

        queryset = self.filter_queryset(queryset)

        # Special filtering for 'status' field
        if 'status' in request.GET:
            status = request.GET['status']

            # First attempt to filter by integer value
            try:
                status = int(status)
                queryset = queryset.filter(status=status)
            except ValueError:
                try:
                    value = OrderStatus.value(status)
                    queryset = queryset.filter(status=value)
                except ValueError:
                    pass

        # Attempt to filter by part
        if 'part' in request.GET:
            try:
                part = Part.objects.get(pk=request.GET['part'])
                queryset = queryset.filter(id__in=[p.id for p in part.purchase_orders()])
            except (Part.DoesNotExist, ValueError):
                pass

        data = queryset.values(
            'pk',
            'supplier',
            'supplier__name',
            'supplier__image',
            'reference',
            'description',
            'URL',
            'status',
            'notes',
            'creation_date',
        )

        for item in data:

            order = queryset.get(pk=item['pk'])

            item['supplier__image'] = os.path.join(settings.MEDIA_URL, item['supplier__image'])
            item['status_text'] = OrderStatus.label(item['status'])
            item['lines'] = order.lines.count()

        return Response(data)

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'supplier',
    ]

    ordering_fields = [
        'creation_date',
        'reference',
    ]

    ordering = '-creation_date'


class PODetail(generics.RetrieveUpdateAPIView):
    """ API endpoint for detail view of a PurchaseOrder object """

    queryset = PurchaseOrder.objects.all()
    serializer_class = POSerializer

    permission_classes = [
        permissions.IsAuthenticated
    ]


class POLineItemList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of PO Line Item objects

    - GET: Return a list of PO Line Item objects
    - POST: Create a new PurchaseOrderLineItem object
    """

    queryset = PurchaseOrderLineItem.objects.all()
    serializer_class = POLineItemSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
    ]

    filter_fields = [
        'order',
        'part'
    ]


class POLineItemDetail(generics.RetrieveUpdateAPIView):
    """ API endpoint for detail view of a PurchaseOrderLineItem object """

    queryset = PurchaseOrderLineItem
    serializer_class = POLineItemSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]


po_api_urls = [
    url(r'^order/(?P<pk>\d+)/?$', PODetail.as_view(), name='api-po-detail'),
    url(r'^order/?$', POList.as_view(), name='api-po-list'),

    url(r'^line/(?P<pk>\d+)/?$', POLineItemDetail.as_view(), name='api-po-line-detail'),
    url(r'^line/?$', POLineItemList.as_view(), name='api-po-line-list'),
]
