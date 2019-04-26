# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics, permissions

from django.db.models import Q
from django.conf.urls import url, include
from django.shortcuts import get_object_or_404

from .models import Part, PartCategory, BomItem
from .models import SupplierPart, SupplierPriceBreak

from .serializers import PartSerializer, BomItemSerializer
from .serializers import SupplierPartSerializer, SupplierPriceBreakSerializer
from .serializers import CategorySerializer

from InvenTree.views import TreeSerializer


class PartCategoryTree(TreeSerializer):

    title = "Parts"
    model = PartCategory


class CategoryList(generics.ListCreateAPIView):
    queryset = PartCategory.objects.all()
    serializer_class = CategorySerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    filter_backends = [
        DjangoFilterBackend,
        # filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'parent',
    ]

    ordering_fields = [
        'name',
    ]

    ordering = 'name'

    search_fields = [
        'name',
        'description',
    ]


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    queryset = PartCategory.objects.all()


class PartDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Part.objects.all()
    serializer_class = PartSerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]


class PartList(generics.ListCreateAPIView):

    serializer_class = PartSerializer

    def get_queryset(self):

        # Does the user wish to filter by category?
        cat_id = self.request.query_params.get('category', None)

        # Start with all objects
        parts_list = Part.objects.all()

        if cat_id:
            category = get_object_or_404(PartCategory, pk=cat_id)

            # Filter by the supplied category
            flt = Q(category=cat_id)

            if self.request.query_params.get('include_child_categories', None):
                childs = category.getUniqueChildren()
                for child in childs:
                    # Ignore the top-level category (already filtered)
                    if str(child) == str(cat_id):
                        continue
                    flt |= Q(category=child)

            parts_list = parts_list.filter(flt)

        return parts_list

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'buildable',
        'consumable',
        'trackable',
        'purchaseable',
        'salable',
    ]

    ordering_fields = [
        'name',
    ]

    ordering = 'name'

    search_fields = [
        '$name',
        'description',
    ]


class BomList(generics.ListCreateAPIView):

    queryset = BomItem.objects.all()
    serializer_class = BomItemSerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'part',
        'sub_part'
    ]


class BomDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = BomItem.objects.all()
    serializer_class = BomItemSerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]


class SupplierPartList(generics.ListCreateAPIView):

    queryset = SupplierPart.objects.all()
    serializer_class = SupplierPartSerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
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


class SupplierPartDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = SupplierPart.objects.all()
    serializer_class = SupplierPartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    read_only_fields = [
    ]


class SupplierPriceBreakList(generics.ListCreateAPIView):

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    filter_backends = [
        DjangoFilterBackend,
    ]

    filter_fields = [
        'part',
    ]


cat_api_urls = [

    url(r'^(?P<pk>\d+)/?', CategoryDetail.as_view(), name='api-part-category-detail'),

    url(r'^$', CategoryList.as_view(), name='api-part-category-list'),
]

supplier_part_api_urls = [

    url(r'^(?P<pk>\d+)/?', SupplierPartDetail.as_view(), name='api-supplier-part-detail'),

    # Catch anything else
    url(r'^.*$', SupplierPartList.as_view(), name='api-part-supplier-list'),
]

part_api_urls = [
    url(r'^tree/?', PartCategoryTree.as_view(), name='api-part-tree'),

    url(r'^category/', include(cat_api_urls)),
    url(r'^supplier/', include(supplier_part_api_urls)),

    url(r'^price-break/?', SupplierPriceBreakList.as_view(), name='api-part-supplier-price'),

    url(r'^(?P<pk>\d+)/', PartDetail.as_view(), name='api-part-detail'),

    url(r'^.*$', PartList.as_view(), name='api-part-list'),
]

bom_api_urls = [
    # BOM Item Detail
    url('^(?P<pk>\d+)/?', BomDetail.as_view(), name='api-bom-detail'),

    # Catch-all
    url(r'^.*$', BomList.as_view(), name='api-bom-list'),
]
