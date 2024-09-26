"""JSON serializers for plugin app."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from common.serializers import GenericReferencedSettingSerializer
from plugin.models import NotificationUserSetting, PluginConfig, PluginSetting


class MetadataSerializer(serializers.ModelSerializer):
    """Serializer class for model metadata API access."""

    metadata = serializers.JSONField(required=True)

    class Meta:
        """Metaclass options."""

        fields = ['metadata']

    def __init__(self, model_type, *args, **kwargs):
        """Initialize the metadata serializer with information on the model type."""
        self.Meta.model = model_type
        super().__init__(*args, **kwargs)

    def update(self, instance, data):
        """Perform update on the metadata field.

        Rules:
        - If this is a partial (PATCH) update, try to 'merge' data in
        - Else, if it is a PUT update, overwrite any existing metadata
        """
        if self.partial:
            # Default behaviour is to "merge" new data in
            metadata = instance.metadata.copy() if instance.metadata else {}
            metadata.update(data['metadata'])
            data['metadata'] = metadata

        return super().update(instance, data)


class PluginConfigSerializer(serializers.ModelSerializer):
    """Serializer for a PluginConfig."""

    class Meta:
        """Meta for serializer."""

        model = PluginConfig
        fields = [
            'pk',
            'key',
            'name',
            'package_name',
            'active',
            'meta',
            'mixins',
            'is_builtin',
            'is_sample',
            'is_installed',
            'is_package',
        ]

        read_only_fields = ['key', 'is_builtin', 'is_sample', 'is_installed']

    meta = serializers.DictField(read_only=True)
    mixins = serializers.DictField(read_only=True)


class PluginConfigInstallSerializer(serializers.Serializer):
    """Serializer for installing a new plugin."""

    class Meta:
        """Meta for serializer."""

        fields = ['url', 'packagename', 'confirm']

    url = serializers.CharField(
        required=False,
        allow_blank=True,
        label=_('Source URL'),
        help_text=_(
            'Source for the package - this can be a custom registry or a VCS path'
        ),
    )

    packagename = serializers.CharField(
        required=False,
        allow_blank=True,
        label=_('Package Name'),
        help_text=_(
            'Name for the Plugin Package - can also contain a version indicator'
        ),
    )

    version = serializers.CharField(
        required=False,
        allow_blank=True,
        label=_('Version'),
        help_text=_(
            'Version specifier for the plugin. Leave blank for latest version.'
        ),
    )

    confirm = serializers.BooleanField(
        label=_('Confirm plugin installation'),
        help_text=_(
            'This will install this plugin now into the current instance. The instance will go into maintenance.'
        ),
    )

    def validate(self, data):
        """Validate inputs.

        Make sure both confirm and url are provided.
        """
        super().validate(data)

        # check the base requirements are met
        if not data.get('confirm'):
            raise ValidationError({'confirm': _('Installation not confirmed')})
        if (not data.get('url')) and (not data.get('packagename')):
            msg = _('Either packagename of URL must be provided')
            raise ValidationError({'url': msg, 'packagename': msg})

        return data

    def save(self):
        """Install a plugin from a package registry and set operational results as instance data."""
        from plugin.installer import install_plugin

        data = self.validated_data

        packagename = data.get('packagename', '')
        url = data.get('url', '')
        version = data.get('version', None)
        user = self.context['request'].user

        return install_plugin(
            url=url, packagename=packagename, version=version, user=user
        )


class PluginConfigEmptySerializer(serializers.Serializer):
    """Serializer for a PluginConfig."""


class PluginReloadSerializer(serializers.Serializer):
    """Serializer for remotely forcing plugin registry reload."""

    class Meta:
        """Meta for serializer."""

        fields = ['full_reload', 'force_reload', 'collect_plugins']

    full_reload = serializers.BooleanField(
        required=False,
        default=False,
        label=_('Full reload'),
        help_text=_('Perform a full reload of the plugin registry'),
    )

    force_reload = serializers.BooleanField(
        required=False,
        default=False,
        label=_('Force reload'),
        help_text=_(
            'Force a reload of the plugin registry, even if it is already loaded'
        ),
    )

    collect_plugins = serializers.BooleanField(
        required=False,
        default=False,
        label=_('Collect plugins'),
        help_text=_('Collect plugins and add them to the registry'),
    )

    def save(self):
        """Reload the plugin registry."""
        from plugin.registry import registry

        registry.reload_plugins(
            full_reload=self.validated_data.get('full_reload', False),
            force_reload=self.validated_data.get('force_reload', False),
            collect=self.validated_data.get('collect_plugins', False),
        )


class PluginActivateSerializer(serializers.Serializer):
    """Serializer for activating or deactivating a plugin."""

    model = PluginConfig

    class Meta:
        """Metaclass for serializer."""

        fields = ['active']

    active = serializers.BooleanField(
        required=False,
        default=True,
        label=_('Activate Plugin'),
        help_text=_('Activate this plugin'),
    )

    def update(self, instance, validated_data):
        """Apply the new 'active' value to the plugin instance."""
        instance.activate(validated_data.get('active', True))
        return instance


class PluginUninstallSerializer(serializers.Serializer):
    """Serializer for uninstalling a plugin."""

    class Meta:
        """Metaclass for serializer."""

        fields = ['delete_config']

    delete_config = serializers.BooleanField(
        required=False,
        default=True,
        label=_('Delete configuration'),
        help_text=_('Delete the plugin configuration from the database'),
    )

    def update(self, instance, validated_data):
        """Uninstall the specified plugin."""
        from plugin.installer import uninstall_plugin

        return uninstall_plugin(
            instance,
            user=self.context['request'].user,
            delete_config=validated_data.get('delete_config', True),
        )


class PluginSettingSerializer(GenericReferencedSettingSerializer):
    """Serializer for the PluginSetting model."""

    MODEL = PluginSetting
    EXTRA_FIELDS = ['plugin']

    plugin = serializers.CharField(source='plugin.key', read_only=True)


class NotificationUserSettingSerializer(GenericReferencedSettingSerializer):
    """Serializer for the PluginSetting model."""

    MODEL = NotificationUserSetting
    EXTRA_FIELDS = ['method']

    method = serializers.CharField(read_only=True)
    typ = serializers.CharField(read_only=True)


class PluginRegistryErrorSerializer(serializers.Serializer):
    """Serializer for a plugin registry error."""

    class Meta:
        """Meta for serializer."""

        fields = ['stage', 'name', 'message']

    stage = serializers.CharField()
    name = serializers.CharField()
    message = serializers.CharField()


class PluginRegistryStatusSerializer(serializers.Serializer):
    """Serializer for plugin registry status."""

    class Meta:
        """Meta for serializer."""

        fields = ['active_plugins', 'registry_errors']

    active_plugins = serializers.IntegerField(read_only=True)
    registry_errors = serializers.ListField(child=PluginRegistryErrorSerializer())


class PluginRelationSerializer(serializers.PrimaryKeyRelatedField):
    """Serializer for a plugin field. Uses the 'slug' of the plugin as the lookup."""

    def __init__(self, **kwargs):
        """Custom init routine for the serializer."""
        kwargs['pk_field'] = 'key'
        kwargs['queryset'] = PluginConfig.objects.all()

        super().__init__(**kwargs)

    def use_pk_only_optimization(self):
        """Disable the PK optimization."""
        return False

    def to_internal_value(self, data):
        """Lookup the PluginConfig object based on the slug."""
        return PluginConfig.objects.filter(key=data).first()

    def to_representation(self, value):
        """Return the 'key' of the PluginConfig object."""
        return value.key
