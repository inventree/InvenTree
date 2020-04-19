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
from InvenTree.helpers import str2bool

import os

from part.models import Part
from company.models import SupplierPart

from .models import PurchaseOrder, PurchaseOrderLineItem
from .serializers import POSerializer, POLineItemSerializer


class POList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of Order objects

    - GET: Return list of PO objects (with filters)
    - POST: Create a new PurchaseOrder object
    """

    queryset = PurchaseOrder.objects.all()
    serializer_class = POSerializer

    def get_serializer(self, *args, **kwargs):

        try:
            kwargs['supplier_detail'] = str2bool(self.request.query_params.get('supplier_detail', False))
        except AttributeError:
            pass

        # Ensure the request context is passed through
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'supplier',
            'lines',
        )

        queryset = POSerializer.annotate_queryset(queryset)

        return queryset


    def filter_queryset(self, queryset):

        # Perform basic filtering
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Special filtering for 'status' field
        status = params.get('status', None)

        if status is not None:
            # First attempt to filter by integer value
            queryset = queryset.filter(status=status)

        # Attempt to filter by part
        part = params.get('part', None)

        if part is not None:
            try:
                part = Part.objects.get(pk=part)
                queryset = queryset.filter(id__in=[p.id for p in part.purchase_orders()])
            except (Part.DoesNotExist, ValueError):
                pass

        # Attempt to filter by supplier part
        supplier_part = params.get('supplier_part', None)

        if supplier_part is not None:
            try:
                supplier_part = SupplierPart.objects.get(pk=supplier_part)
                queryset = queryset.filter(id__in=[p.id for p in supplier_part.purchase_orders()])
            except (ValueError, SupplierPart.DoesNotExist):
                pass

        return queryset

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

    def get_serializer(self, *args, **kwargs):

        try:
            kwargs['supplier_detail'] = str2bool(self.request.query_params.get('supplier_detail', False))
        except AttributeError:
            pass

        # Ensure the request context is passed through
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'supplier',
            'lines',
        )

        queryset = POSerializer.annotate_queryset(queryset)

        return queryset

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
