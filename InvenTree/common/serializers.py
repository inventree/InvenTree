"""
JSON serializers for common components
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.serializers import InvenTreeModelSerializer

from rest_framework import serializers

from common.models import InvenTreeSetting, InvenTreeUserSetting


class SettingsSerializer(InvenTreeModelSerializer):
    """
    Base serializer for a settings object
    """

    key = serializers.CharField(read_only=True)

    name = serializers.CharField(read_only=True)

    description = serializers.CharField(read_only=True)

    type = serializers.CharField(source='setting_type', read_only=True)

    choices = serializers.SerializerMethodField()

    def get_choices(self, obj):
        """
        Returns the choices available for a given item
        """

        return obj.choices()


class GlobalSettingsSerializer(SettingsSerializer):
    """
    Serializer for the InvenTreeSetting model
    """

    class Meta:
        model = InvenTreeSetting
        fields = [
            'pk',
            'key',
            'value',
            'name',
            'description',
            'type',
            'choices',
        ]


class UserSettingsSerializer(SettingsSerializer):
    """
    Serializer for the InvenTreeUserSetting model
    """

    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = InvenTreeUserSetting
        fields = [
            'pk',
            'key',
            'value',
            'name',
            'description',
            'user',
            'type',
            'choices',
        ]
