"""
JSON serializers for common components
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.serializers import InvenTreeModelSerializer
from InvenTree.helpers import get_objectreference

from rest_framework import serializers

from common.models import InvenTreeSetting, InvenTreeUserSetting, NotificationMessage


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

        results = []

        choices = obj.choices()

        if choices:
            for choice in choices:
                results.append({
                    'value': choice[0],
                    'display_name': choice[1],
                })

        return results

    def get_value(self, obj):
        """
        Make sure protected values are not returned
        """
        result = obj.value

        # never return protected values
        if obj.is_protected:
            result = '***'

        return result


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


class NotificationMessageSerializer(SettingsSerializer):
    """
    Serializer for the InvenTreeUserSetting model
    """

    target = serializers.SerializerMethodField()

    source = serializers.SerializerMethodField()

    user = serializers.PrimaryKeyRelatedField(read_only=True)

    category = serializers.CharField(read_only=True)

    name = serializers.CharField(read_only=True)

    message = serializers.CharField(read_only=True)

    creation = serializers.CharField(read_only=True)

    age = serializers.IntegerField()

    age_human = serializers.CharField()

    read = serializers.BooleanField()

    def get_target(self, obj):
        return get_objectreference(obj, 'target_content_type', 'target_object_id')

    def get_source(self, obj):
        return get_objectreference(obj, 'source_content_type', 'source_object_id')

    class Meta:
        model = NotificationMessage
        fields = [
            'pk',
            'target',
            'source',
            'user',
            'category',
            'name',
            'message',
            'creation',
            'age',
            'age_human',
            'read',
        ]
