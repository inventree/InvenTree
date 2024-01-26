from typing import List, Union

from rest_framework import serializers

from common.serializers import GenericReferencedSettingSerializer
from InvenTree.helpers_mixin import ClassProviderMixin
from machine.models import MachineConfig, MachineSetting


class MachineConfigSerializer(serializers.ModelSerializer):
    """Serializer for a MachineConfig."""

    class Meta:
        """Meta for serializer."""

        model = MachineConfig
        fields = [
            'pk',
            'name',
            'machine_type',
            'driver',
            'initialized',
            'active',
            'status',
            'status_model',
            'status_text',
            'machine_errors',
            'is_driver_available',
        ]

        read_only_fields = ['machine_type', 'driver']

    initialized = serializers.SerializerMethodField('get_initialized')
    status = serializers.SerializerMethodField('get_status')
    status_model = serializers.SerializerMethodField('get_status_model')
    status_text = serializers.SerializerMethodField('get_status_text')
    machine_errors = serializers.SerializerMethodField('get_errors')
    is_driver_available = serializers.SerializerMethodField('get_is_driver_available')

    def get_initialized(self, obj: MachineConfig) -> bool:
        return getattr(obj.machine, 'initialized', False)

    def get_status(self, obj: MachineConfig) -> int:
        status = getattr(obj.machine, 'status', None)
        if status is not None:
            return status.value
        return -1

    def get_status_model(self, obj: MachineConfig) -> Union[str, None]:
        if obj.machine and obj.machine.MACHINE_STATUS:
            return obj.machine.MACHINE_STATUS.__name__
        return None

    def get_status_text(self, obj: MachineConfig) -> str:
        return getattr(obj.machine, 'status_text', '')

    def get_errors(self, obj: MachineConfig) -> List[str]:
        return [str(err) for err in obj.errors]

    def get_is_driver_available(self, obj: MachineConfig) -> bool:
        return obj.is_driver_available()


class MachineConfigCreateSerializer(MachineConfigSerializer):
    """Serializer for creating a MachineConfig."""

    class Meta(MachineConfigSerializer.Meta):
        """Meta for serializer."""

        read_only_fields = list(
            set(MachineConfigSerializer.Meta.read_only_fields)
            - set(['machine_type', 'driver'])
        )


class MachineSettingSerializer(GenericReferencedSettingSerializer):
    """Serializer for the MachineSetting model."""

    MODEL = MachineSetting
    EXTRA_FIELDS = ['config_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # remove unwanted fields
        unwanted_fields = ['pk', 'model_name', 'api_url', 'typ']
        for f in unwanted_fields:
            if f in self.Meta.fields:
                self.Meta.fields.remove(f)

        self.Meta.read_only_fields = ['config_type']


class BaseMachineClassSerializer(serializers.Serializer):
    """Serializer for a BaseClass."""

    class Meta:
        """Meta for a serializer."""

        fields = [
            'slug',
            'name',
            'description',
            'provider_file',
            'provider_plugin',
            'is_builtin',
        ]

        read_only_fields = fields

    slug = serializers.SlugField(source='SLUG')
    name = serializers.CharField(source='NAME')
    description = serializers.CharField(source='DESCRIPTION')
    provider_file = serializers.SerializerMethodField('get_provider_file')
    provider_plugin = serializers.SerializerMethodField('get_provider_plugin')
    is_builtin = serializers.SerializerMethodField('get_is_builtin')

    def get_provider_file(self, obj: ClassProviderMixin) -> str:
        return obj.get_provider_file()

    def get_provider_plugin(self, obj: ClassProviderMixin) -> Union[dict, None]:
        plugin = obj.get_provider_plugin()
        if plugin:
            return {
                'slug': plugin.slug,
                'name': plugin.human_name,
                'pk': getattr(plugin.plugin_config(), 'pk', None),
            }
        return None

    def get_is_builtin(self, obj: ClassProviderMixin) -> bool:
        return obj.get_is_builtin()


class MachineTypeSerializer(BaseMachineClassSerializer):
    """Serializer for a BaseMachineType class."""

    class Meta(BaseMachineClassSerializer.Meta):
        """Meta for a serializer."""

        fields = [*BaseMachineClassSerializer.Meta.fields]


class MachineDriverSerializer(BaseMachineClassSerializer):
    """Serializer for a BaseMachineDriver class."""

    class Meta(BaseMachineClassSerializer.Meta):
        """Meta for a serializer."""

        fields = [*BaseMachineClassSerializer.Meta.fields, 'machine_type']

    machine_type = serializers.SlugField(read_only=True)


class MachineRegistryErrorSerializer(serializers.Serializer):
    """Serializer for a machine registry error."""

    class Meta:
        fields = ['message']

    message = serializers.CharField()


class MachineRegistryStatusSerializer(serializers.Serializer):
    """Serializer for machine registry status."""

    class Meta:
        fields = ['registry_errors']

    registry_errors = serializers.ListField(child=MachineRegistryErrorSerializer())
