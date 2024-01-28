"""Serializers for the machine app."""

from typing import List, Union

from rest_framework import serializers

from common.serializers import GenericReferencedSettingSerializer
from InvenTree.helpers_mixin import ClassProviderMixin
from machine import registry
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
            'restart_required',
        ]

        read_only_fields = ['machine_type', 'driver']

    initialized = serializers.SerializerMethodField('get_initialized')
    status = serializers.SerializerMethodField('get_status')
    status_model = serializers.SerializerMethodField('get_status_model')
    status_text = serializers.SerializerMethodField('get_status_text')
    machine_errors = serializers.SerializerMethodField('get_errors')
    is_driver_available = serializers.SerializerMethodField('get_is_driver_available')
    restart_required = serializers.SerializerMethodField('get_restart_required')

    def get_initialized(self, obj: MachineConfig) -> bool:
        """Serializer method for the initialized field."""
        return getattr(obj.machine, 'initialized', False)

    def get_status(self, obj: MachineConfig) -> int:
        """Serializer method for the status field."""
        status = getattr(obj.machine, 'status', None)
        if status is not None:
            return status.value
        return -1

    def get_status_model(self, obj: MachineConfig) -> Union[str, None]:
        """Serializer method for the status model field."""
        if obj.machine and obj.machine.MACHINE_STATUS:
            return obj.machine.MACHINE_STATUS.__name__
        return None

    def get_status_text(self, obj: MachineConfig) -> str:
        """Serializer method for the status text field."""
        return getattr(obj.machine, 'status_text', '')

    def get_errors(self, obj: MachineConfig) -> List[str]:
        """Serializer method for the errors field."""
        return [str(err) for err in obj.errors]

    def get_is_driver_available(self, obj: MachineConfig) -> bool:
        """Serializer method for the is_driver_available field."""
        return obj.is_driver_available()

    def get_restart_required(self, obj: MachineConfig) -> bool:
        """Serializer method for the restart_required field."""
        return getattr(obj.machine, 'restart_required', False)


class MachineConfigCreateSerializer(MachineConfigSerializer):
    """Serializer for creating a MachineConfig."""

    class Meta(MachineConfigSerializer.Meta):
        """Meta for serializer."""

        read_only_fields = list(
            set(MachineConfigSerializer.Meta.read_only_fields)
            - {'machine_type', 'driver'}
        )


class MachineSettingSerializer(GenericReferencedSettingSerializer):
    """Serializer for the MachineSetting model."""

    MODEL = MachineSetting
    EXTRA_FIELDS = ['config_type']

    def __init__(self, *args, **kwargs):
        """Custom init method to remove unwanted fields."""
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
        """Serializer method for the provider_file field."""
        return obj.get_provider_file()

    def get_provider_plugin(self, obj: ClassProviderMixin) -> Union[dict, None]:
        """Serializer method for the provider_plugin field."""
        plugin = obj.get_provider_plugin()
        if plugin:
            return {
                'slug': plugin.slug,
                'name': plugin.human_name,
                'pk': getattr(plugin.plugin_config(), 'pk', None),
            }
        return None

    def get_is_builtin(self, obj: ClassProviderMixin) -> bool:
        """Serializer method for the is_builtin field."""
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

        fields = [*BaseMachineClassSerializer.Meta.fields, 'machine_type', 'errors']

    machine_type = serializers.SlugField(read_only=True)

    driver_errors = serializers.SerializerMethodField('get_errors')

    def get_errors(self, obj) -> List[str]:
        """Serializer method for the errors field."""
        driver_instance = registry.driver_instances.get(obj.SLUG, None)
        if driver_instance is None:
            return []
        return [str(err) for err in driver_instance.errors]


class MachineRegistryErrorSerializer(serializers.Serializer):
    """Serializer for a machine registry error."""

    class Meta:
        """Meta for a serializer."""

        fields = ['message']

    message = serializers.CharField()


class MachineRegistryStatusSerializer(serializers.Serializer):
    """Serializer for machine registry status."""

    class Meta:
        """Meta for a serializer."""

        fields = ['registry_errors']

    registry_errors = serializers.ListField(child=MachineRegistryErrorSerializer())


class MachineRestartSerializer(serializers.Serializer):
    """Serializer for the machine restart response."""

    class Meta:
        """Meta for a serializer."""

        fields = ['ok']

    ok = serializers.BooleanField()
