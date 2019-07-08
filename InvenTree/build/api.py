"""
JSON API for the Build app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics, permissions

from django.conf.urls import url, include

from .models import Build, BuildItem
from .serializers import BuildSerializer, BuildItemSerializer


class BuildList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of Build objects.
    
    - GET: Return list of objects (with filters)
    - POST: Create a new Build object
    """

    queryset = Build.objects.all()
    serializer_class = BuildSerializer

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
    ]


class BuildDetail(generics.RetrieveUpdateAPIView):
    """ API endpoint for detail view of a Build object """

    queryset = Build.objects.all()
    serializer_class = BuildSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]


class BuildItemList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of BuildItem objects

    - GET: Return list of objects
    - POST: Create a new BuildItem object
    """

    serializer_class = BuildItemSerializer

    def get_queryset(self):
        """ Override the queryset method,
        to allow filtering by stock_item.part
        """

        # Does the user wish to filter by part?
        part_pk = self.request.query_params.get('part', None)

        query = BuildItem.objects.all()

        query = query.select_related('stock_item')
        query = query.prefetch_related('stock_item__part')
        query = query.prefetch_related('stock_item__part__category')

        if part_pk:
            query = query.filter(stock_item__part=part_pk)

        return query

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
    ]

    filter_fields = [
        'build',
        'stock_item'
    ]


build_item_api_urls = [
    url('^.*$', BuildItemList.as_view(), name='api-build-item-list'),
]

build_api_urls = [
    url(r'^item/?', include(build_item_api_urls)),

    url(r'^(?P<pk>\d+)/', BuildDetail.as_view(), name='api-build-detail'),

    url(r'^.*$', BuildList.as_view(), name='api-build-list'),
]
