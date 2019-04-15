# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics, permissions

from django.conf.urls import url, include

from .models import Build
from .serializers import BuildSerializer


class BuildList(generics.ListAPIView):

    queryset = Build.objects.all()
    serializer_class = BuildSerializer

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
    ]

build_api_urls = [
    url(r'^.*$', BuildList.as_view(), name='api-build-list')
]