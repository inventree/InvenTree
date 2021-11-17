"""
JSON serializers for Stock app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from plugin.models import PluginConfig


class PluginConfigSerializer(serializers.ModelSerializer):
    """ Serializer for a PluginConfig:
    """

    meta = serializers.DictField(read_only=True)

    class Meta:
        model = PluginConfig
        fields = [
            'key',
            'name',
            'active',
            'meta',
        ]
