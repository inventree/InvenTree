"""
Provides a JSON API for common components.
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import permissions, generics, filters

from django.conf.urls import url

from .models import Currency
from .serializers import CurrencySerializer


class CurrencyList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of Currency objects.

    - GET: Return a list of Currencies
    - POST: Create a new currency
    """

    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        filters.OrderingFilter,
    ]

    ordering_fields = ['suffix', 'value']


common_api_urls = [
    url(r'^currency/?$', CurrencyList.as_view(), name='api-currency-list'),
]
