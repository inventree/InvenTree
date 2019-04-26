# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics, permissions

from django.conf.urls import url

from .models import Company
from .serializers import CompanySerializer


class CompanyList(generics.ListCreateAPIView):

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

    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]


company_api_urls = [

    url(r'^(?P<pk>\d+)/?', CompanyDetail.as_view(), name='api-company-detail'),

    url(r'^.*$', CompanyList.as_view(), name='api-company-list'),
]
