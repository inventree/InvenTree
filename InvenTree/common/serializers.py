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

    key = serializers.CharField(read_only=True)

    name = serializers.CharField(read_only=True)

    description = serializers.CharField(read_only=True)

    type = serializers.CharField(source='setting_type', read_only=True)

    choices = serializers.SerializerMethodField()

    def get_choices(self, obj: InvenTreeUserSetting):
        """
        Returns the choices available for a given item
        """

        return obj.choices()

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


class UserSettingsSerializer(InvenTreeModelSerializer):
    """
    Serializer for the InvenTreeUserSetting model
    """

    key = serializers.CharField(read_only=True)

    name = serializers.CharField(read_only=True)

    description = serializers.CharField(read_only=True)

    user = serializers.PrimaryKeyRelatedField(read_only=True)

    type = serializers.CharField(source='setting_type', read_only=True)

    choices = serializers.SerializerMethodField()

    def get_choices(self, obj: InvenTreeUserSetting):
        """
        Returns the choices available for a given item
        """

        return obj.choices()

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
