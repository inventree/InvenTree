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


plugin_api_urls = [
    # Anything else
    url(r'^.*$', PluginList.as_view(), name='api-plugin-list'),
]
