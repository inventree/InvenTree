"""
JSON API for the Build app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics

from django.conf.urls import url, include

from InvenTree.helpers import str2bool
from InvenTree.status_codes import BuildStatus

from .models import Build, BuildItem
from .serializers import BuildSerializer, BuildItemSerializer


class BuildList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of Build objects.
    
    - GET: Return list of objects (with filters)
    - POST: Create a new Build object
    """

    queryset = Build.objects.all()
    serializer_class = BuildSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'sales_order',
    ]

    def get_queryset(self):
        """
        Override the queryset filtering,
        as some of the fields don't natively play nicely with DRF
        """

        queryset = super().get_queryset().prefetch_related('part')

        queryset = BuildSerializer.annotate_queryset(queryset)

        return queryset
    
    def filter_queryset(self, queryset):

        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filter by build status?
        status = params.get('status', None)

        if status is not None:
            queryset = queryset.filter(status=status)

        # Filter by "pending" status
        active = params.get('active', None)

        if active is not None:
            active = str2bool(active)

            if active:
                queryset = queryset.filter(status__in=BuildStatus.ACTIVE_CODES)
            else:
                queryset = queryset.exclude(status__in=BuildStatus.ACTIVE_CODES)

        # Filter by "overdue" status?
        overdue = params.get('overdue', None)

        if overdue is not None:
            overdue = str2bool(overdue)

            if overdue:
                queryset = queryset.filter(Build.OVERDUE_FILTER)
            else:
                queryset = queryset.exclude(Build.OVERDUE_FILTER)

        # Filter by associated part?
        part = params.get('part', None)

        if part is not None:
            queryset = queryset.filter(part=part)

        # Filter by 'date range'
        min_date = params.get('min_date', None)
        max_date = params.get('max_date', None)

        if min_date is not None and max_date is not None:
            queryset = Build.filterByDate(queryset, min_date, max_date)

        return queryset

    def get_serializer(self, *args, **kwargs):

        try:
            part_detail = str2bool(self.request.GET.get('part_detail', None))
        except AttributeError:
            part_detail = None

        kwargs['part_detail'] = part_detail

        return self.serializer_class(*args, **kwargs)


class BuildDetail(generics.RetrieveUpdateAPIView):
    """ API endpoint for detail view of a Build object """

    queryset = Build.objects.all()
    serializer_class = BuildSerializer


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

        query = BuildItem.objects.all()

        query = query.select_related('stock_item')
        query = query.prefetch_related('stock_item__part')
        query = query.prefetch_related('stock_item__part__category')

        return query

    def filter_queryset(self, queryset):

        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Does the user wish to filter by part?
        part_pk = params.get('part', None)

        if part_pk:
            queryset = queryset.filter(stock_item__part=part_pk)

        # Filter by output target
        output = params.get('output', None)

        if output:
            queryset = queryset.filter(install_into=output)

        return queryset

    filter_backends = [
        DjangoFilterBackend,
    ]

    filter_fields = [
        'build',
        'stock_item',
        'install_into',
    ]


build_item_api_urls = [
    url('^.*$', BuildItemList.as_view(), name='api-build-item-list'),
]

build_api_urls = [
    url(r'^item/', include(build_item_api_urls)),

    url(r'^(?P<pk>\d+)/', BuildDetail.as_view(), name='api-build-detail'),

    url(r'^.*$', BuildList.as_view(), name='api-build-list'),
]
