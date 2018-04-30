# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics, permissions

from django.conf.urls import url

from .models import Part, PartCategory
from .serializers import PartSerializer

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


part_api_urls = [

    url(r'^tree/?', PartCategoryTree.as_view(), name='api-part-tree'),

    url(r'^.*$', PartList.as_view(), name='api-part-list'),
]
