"""
JSON API for the plugin app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.utils.translation import ugettext_lazy as _

from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response

from plugin.models import PluginConfig
import plugin.serializers as PluginSerializers


class PluginList(generics.ListAPIView):
    """ API endpoint for list of PluginConfig objects

    - GET: Return a list of all PluginConfig objects
    """

    serializer_class = PluginSerializers.PluginConfigSerializer
    queryset = PluginConfig.objects.all()

    ordering_fields = [
        'key',
        'name',
        'active',
    ]

    ordering = [
        'key',
    ]

    search_fields = [
        'key',
        'name',
    ]


class PluginDetail(generics.RetrieveUpdateDestroyAPIView):
    """ API detail endpoint for PluginConfig object

    get:
    Return a single PluginConfig object

    post:
    Update a PluginConfig

    delete:
    Remove a PluginConfig
    """

    queryset = PluginConfig.objects.all()
    serializer_class = PluginSerializers.PluginConfigSerializer


class PluginInstall(generics.CreateAPIView):
    """
    Endpoint for installing a new plugin
    """
    queryset = PluginConfig.objects.none()
    serializer_class = PluginSerializers.PluginConfigInstallSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.perform_create(serializer)
        result['data'] = serializer.data
        headers = self.get_success_headers(serializer.data)
        return Response(result, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()


plugin_api_urls = [
    # Detail views for a single PluginConfig item
    url(r'^(?P<pk>\d+)/', include([
        url(r'^.*$', PluginDetail.as_view(), name='api-plugin-detail'),
    ])),

    url(r'^install/', PluginInstall.as_view(), name='api-plugin-install'),

    # Anything else
    url(r'^.*$', PluginList.as_view(), name='api-plugin-list'),
]
