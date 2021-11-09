"""
JSON serializers for common components
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.serializers import InvenTreeModelSerializer

from rest_framework import serializers

from common.models import InvenTreeSetting, InvenTreeUserSetting

class GlobalSettingsSerializer(InvenTreeModelSerializer):
    """
    Serializer for the InvenTreeSetting model
    """

    name = serializers.CharField(read_only=True)

    description = serializers.CharField(read_only=True)

    # choices = serializers.CharField(read_only=True, many=True)

    class Meta:
        model = InvenTreeSetting
        fields = [
            'pk',
            'key',
            'value',
            'name',
            'description',
            # 'type',
        ]


class UserSettingsSerializer(InvenTreeModelSerializer):
    """
    Serializer for the InvenTreeUserSetting model
    """

    name = serializers.CharField(read_only=True)

    description = serializers.CharField(read_only=True)

    # choices = serializers.CharField(read_only=True, many=True)

    class Meta:
        model = InvenTreeUserSetting
        fields = [
            'pk',
            'key',
            'value',
            'name',
            'description',
            'user',
            # 'type',
        ]
