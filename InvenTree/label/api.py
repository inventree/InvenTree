# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, filters

from .models import StockItemLabel
from .serializers import StockItemLabelSerializer


class StockItemLabelList(generics.ListAPIView):
    """
    API endpoint for viewing list of StockItemLabel objects.
    """

    queryset = StockItemLabel.objects.all()
    serializer_class = StockItemLabelSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter
    ]

    filter_fields = [
        'enabled',
    ]

    search_fields = [
        'name',
        'description',
    ]


label_api_urls = [

    # Stock item labels
    url(r'stock/', include([
        url(r'^.*$', StockItemLabelList.as_view(), name='api-stock-label-list'),
    ])),
]
