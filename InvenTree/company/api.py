"""
Provides a JSON API for the Company app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics, permissions

from django.conf.urls import url, include

from InvenTree.helpers import str2bool

from .models import Company
from .models import SupplierPart, SupplierPriceBreak

from .serializers import CompanySerializer
from .serializers import SupplierPartSerializer, SupplierPriceBreakSerializer


class CompanyList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of Company objects

    Provides two methods:

    - GET: Return list of objects
    - POST: Create a new Company object
    """

    serializer_class = CompanySerializer
    queryset = Company.objects.all()
    
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'name',
        'is_customer',
        'is_supplier',
    ]

    search_fields = [
        'name',
        'description',
    ]

    ordering_fields = [
        'name',
    ]

    ordering = 'name'


class CompanyDetail(generics.RetrieveUpdateDestroyAPIView):
    """ API endpoint for detail of a single Company object """

    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    permission_classes = [
        permissions.IsAuthenticated,
    ]


class SupplierPartList(generics.ListCreateAPIView):
    """ API endpoint for list view of SupplierPart object

    - GET: Return list of SupplierPart objects
    - POST: Create a new SupplierPart object
    """

    queryset = SupplierPart.objects.all().prefetch_related(
        'part',
        'part__category',
        'part__stock_items',
        'part__bom_items',
        'part__builds',
        'supplier',
        'pricebreaks')

    def get_serializer(self, *args, **kwargs):

        # Do we wish to include extra detail?
        try:
            part_detail = str2bool(self.request.GET.get('part_detail', None))
        except AttributeError:
            part_detail = None

        kwargs['part_detail'] = part_detail
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    serializer_class = SupplierPartSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'part',
        'supplier'
    ]

    search_fields = [
        'SKU',
        'supplier__name',
        'manufacturer',
        'description',
        'MPN',
    ]


class SupplierPartDetail(generics.RetrieveUpdateDestroyAPIView):
    """ API endpoint for detail view of SupplierPart object

    - GET: Retrieve detail view
    - PATCH: Update object
    - DELETE: Delete objec
    """

    queryset = SupplierPart.objects.all()
    serializer_class = SupplierPartSerializer
    permission_classes = (permissions.IsAuthenticated,)

    read_only_fields = [
    ]


class SupplierPriceBreakList(generics.ListCreateAPIView):
    """ API endpoint for list view of SupplierPriceBreak object

    - GET: Retrieve list of SupplierPriceBreak objects
    - POST: Create a new SupplierPriceBreak object
    """

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
    ]

    filter_fields = [
        'part',
    ]


supplier_part_api_urls = [

    url(r'^(?P<pk>\d+)/?', SupplierPartDetail.as_view(), name='api-supplier-part-detail'),

    # Catch anything else
    url(r'^.*$', SupplierPartList.as_view(), name='api-part-supplier-list'),
]


company_api_urls = [
    
    url(r'^part/?', include(supplier_part_api_urls)),

    url(r'^price-break/?', SupplierPriceBreakList.as_view(), name='api-part-supplier-price'),

    url(r'^(?P<pk>\d+)/?', CompanyDetail.as_view(), name='api-company-detail'),

    url(r'^.*$', CompanyList.as_view(), name='api-company-list'),
]
