"""
JSON API for the plugin app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from django.utils.translation import ugettext_lazy as _

from rest_framework import generics

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


plugin_api_urls = [
    # Detail views for a single PluginConfig item
    url(r'^(?P<pk>\d+)/', include([
        url(r'^.*$', PluginDetail.as_view(), name='api-plugin-detail'),
    ])),
    # Anything else
    url(r'^.*$', PluginList.as_view(), name='api-plugin-list'),
]
