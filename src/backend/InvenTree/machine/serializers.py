"""Serializers for the machine app."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from common.serializers import GenericReferencedSettingSerializer
from InvenTree.helpers_mixin import ClassProviderMixin
from machine import registry
from machine.machine_type import MachinePropertyType
from machine.models import MachineConfig, MachineSetting


class MachinePropertySerializer(serializers.Serializer):
    """Machine Properties are set by the driver/machine to represent specific state."""

    class Meta:
        """Meta for serializer."""

        fields = ['key', 'value', 'group', 'type', 'max_progress']
        read_only_fields = fields

    key = serializers.CharField(
        label=_('Key'), help_text=_('Key of the property'), required=True
    )
    value = serializers.CharField(
        label=_('Value'), help_text=_('Value of the property'), required=True
    )
    group = serializers.CharField(
        label=_('Group'), help_text=_('Grouping of the property'), required=False
    )
    type = serializers.ChoiceField(
        label=_('Type'),
        choices=MachinePropertyType.__args__,
        help_text=_('Type of the property'),
        default='str',
        required=False,
    )
    max_progress = serializers.IntegerField(
        label=_('Max Progress'),
        help_text=_('Maximum value for progress type, required if type=progress'),
        required=False,
        allow_null=True,
    )


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
            'properties',
        ]

        read_only_fields = ['machine_type', 'driver', 'properties']

    initialized = serializers.SerializerMethodField('get_initialized')
    status = serializers.SerializerMethodField('get_status')
    status_model = serializers.SerializerMethodField('get_status_model')
    status_text = serializers.SerializerMethodField('get_status_text')
    machine_errors = serializers.SerializerMethodField('get_errors')
    is_driver_available = serializers.SerializerMethodField('get_is_driver_available')
    restart_required = serializers.SerializerMethodField('get_restart_required')
    properties = serializers.ListField(
        child=MachinePropertySerializer(),
        source='machine.properties',
        read_only=True,
        default=[],
    )

    def get_initialized(self, obj: MachineConfig) -> bool:
        """Indicator if machine is initialized."""
        return getattr(obj.machine, 'initialized', False)

    def get_status(self, obj: MachineConfig) -> int:
        """Numerical machine status if available, else -1."""
        status = getattr(obj.machine, 'status', None)
        if status is not None:
            return status.value
        return -1

    def get_status_model(self, obj: MachineConfig) -> str | None:
        """Textual machine status name if available, else None."""
        if obj.machine and obj.machine.MACHINE_STATUS:
            return obj.machine.MACHINE_STATUS.__name__

    def get_status_text(self, obj: MachineConfig) -> str:
        """Current status text for machine."""
        return getattr(obj.machine, 'status_text', '')

    def get_errors(self, obj: MachineConfig) -> list[str]:
        """List of machine errors."""
        return [str(err) for err in obj.errors]

    def get_is_driver_available(self, obj: MachineConfig) -> bool:
        """Indicator if driver for machine is available."""
        return obj.is_driver_available()

    def get_restart_required(self, obj: MachineConfig) -> bool:
        """Indicator if machine restart is required."""
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
        """Custom init method to make the config_type field read only."""
        super().__init__(*args, **kwargs)

        self.Meta.read_only_fields = ['config_type']  # type: ignore


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
        """File that contains the class definition."""
        return obj.get_provider_file()

    def get_provider_plugin(self, obj: ClassProviderMixin) -> dict | None:
        """Plugin(s) that contain(s) the class definition."""
        plugin = obj.get_provider_plugin()
        if plugin:
            return {
                'slug': plugin.slug,
                'name': plugin.human_name,
                'pk': getattr(plugin.plugin_config(), 'pk', None),
            }
        return None

    def get_is_builtin(self, obj: ClassProviderMixin) -> bool:
        """Indicates if the machine type is build into the InvenTree source code."""
        return obj.get_is_builtin()


class MachineTypeSerializer(BaseMachineClassSerializer):
    """Available machine types."""

    class Meta(BaseMachineClassSerializer.Meta):
        """Meta for a serializer."""

        fields = [*BaseMachineClassSerializer.Meta.fields]


class MachineDriverSerializer(BaseMachineClassSerializer):
    """Machine drivers."""

    class Meta(BaseMachineClassSerializer.Meta):
        """Meta for a serializer."""

        fields = [*BaseMachineClassSerializer.Meta.fields, 'machine_type', 'errors']

    machine_type = serializers.SlugField(read_only=True)

    driver_errors = serializers.SerializerMethodField('get_errors')

    def get_errors(self, obj) -> list[str]:
        """Errors registered against driver."""
        driver_instance = registry.get_driver_instance(obj.SLUG)

        if driver_instance is None:
            return []
        return [str(err) for err in driver_instance.errors]


class MachineRegistryErrorSerializer(serializers.Serializer):
    """Machine registry error."""

    class Meta:
        """Meta for a serializer."""

        fields = ['message']

    message = serializers.CharField()


class MachineRegistryStatusSerializer(serializers.Serializer):
    """Machine registry status, showing all errors that were registered."""

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
