"""JSON serializers for common components."""

from rest_framework import serializers

from common.models import (InvenTreeSetting, InvenTreeUserSetting,
                           NotificationMessage)
from InvenTree.helpers import get_objectreference
from InvenTree.serializers import InvenTreeModelSerializer


class SettingsSerializer(InvenTreeModelSerializer):
    """Base serializer for a settings object."""

    key = serializers.CharField(read_only=True)

    name = serializers.CharField(read_only=True)

    description = serializers.CharField(read_only=True)

    type = serializers.CharField(source='setting_type', read_only=True)

    choices = serializers.SerializerMethodField()

    model_name = serializers.CharField(read_only=True)

    api_url = serializers.CharField(read_only=True)

    def get_choices(self, obj):
        """Returns the choices available for a given item."""
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
        """Make sure protected values are not returned."""
        # never return protected values
        if obj.protected:
            result = '***'
        else:
            result = obj.value

        return result


class GlobalSettingsSerializer(SettingsSerializer):
    """Serializer for the InvenTreeSetting model."""

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
            'model_name',
            'api_url',
        ]


class UserSettingsSerializer(SettingsSerializer):
    """Serializer for the InvenTreeUserSetting model."""

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
            'model_name',
            'api_url',
        ]


class GenericReferencedSettingSerializer(SettingsSerializer):
    """Serializer for a GenericReferencedSetting model.

    Args:
        MODEL: model class for the serializer
        EXTRA_FIELDS: fields that need to be appended to the serializer
            field must also be defined in the custom class
    """

    MODEL = None
    EXTRA_FIELDS = None

    def __init__(self, *args, **kwargs):
        """Init overrides the Meta class to make it dynamic."""
        class CustomMeta:
            """Scaffold for custom Meta class."""
            fields = [
                'pk',
                'key',
                'value',
                'name',
                'description',
                'type',
                'choices',
                'model_name',
                'api_url',
            ]

        # set Meta class
        self.Meta = CustomMeta
        self.Meta.model = self.MODEL
        # extend the fields
        self.Meta.fields.extend(self.EXTRA_FIELDS)

        # resume operations
        super().__init__(*args, **kwargs)


class NotificationMessageSerializer(InvenTreeModelSerializer):
    """Serializer for the InvenTreeUserSetting model."""

    target = serializers.SerializerMethodField(read_only=True)

    source = serializers.SerializerMethodField(read_only=True)

    user = serializers.PrimaryKeyRelatedField(read_only=True)

    category = serializers.CharField(read_only=True)

    name = serializers.CharField(read_only=True)

    message = serializers.CharField(read_only=True)

    creation = serializers.CharField(read_only=True)

    age = serializers.IntegerField(read_only=True)

    age_human = serializers.CharField(read_only=True)

    read = serializers.BooleanField(read_only=True)

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


class NotificationReadSerializer(NotificationMessageSerializer):

    def is_valid(self, raise_exception=False):
        self.instance = self.context['instance']  # set instance that should be returned
        self._validated_data = True
        return True
