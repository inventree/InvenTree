"""
Provides a JSON API for the Company app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics, permissions

from django.conf.urls import url

from .models import Company
from .serializers import CompanySerializer


class CompanyList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of Company objects

    Provides two methods:

    - GET: Return list of objects
    - POST: Create a new Company object
    """

    serializer_class = CompanySerializer
    queryset = Company.objects.all()
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
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
        permissions.IsAuthenticatedOrReadOnly,
    ]


company_api_urls = [

    url(r'^(?P<pk>\d+)/?', CompanyDetail.as_view(), name='api-company-detail'),

    url(r'^.*$', CompanyList.as_view(), name='api-company-list'),
]
