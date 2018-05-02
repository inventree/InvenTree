# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics, permissions

from django.conf.urls import url

from .models import Part, PartCategory, BomItem
from .models import SupplierPart

from .serializers import PartSerializer, BomItemSerializer
from .serializers import SupplierPartSerializer

from InvenTree.views import TreeSerializer

class PartCategoryTree(TreeSerializer):

    title = "Parts"
    model = PartCategory


class PartList(generics.ListCreateAPIView):

    queryset = Part.objects.all()
    serializer_class = PartSerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'category',
    ]

    ordering_fields = [
        'name',
    ]

    ordering = 'name'

    search_fields = [
        'name',
        'description',
    ]


class BomList(generics.ListAPIView):

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


class SupplierPartList(generics.ListAPIView):

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


part_api_urls = [

    url(r'^tree/?', PartCategoryTree.as_view(), name='api-part-tree'),

    url(r'^supplier/?', SupplierPartList.as_view(), name='api-part-supplier-list'),
    url(r'^bom/?', BomList.as_view(), name='api-bom-list'),
    url(r'^.*$', PartList.as_view(), name='api-part-list'),
]
