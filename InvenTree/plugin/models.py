"""Plugin model definitions."""

import warnings

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

import common.models
from plugin import InvenTreePlugin, registry


class MetadataMixin(models.Model):
    """Model mixin class which adds a JSON metadata field to a model, for use by any (and all) plugins.

    The intent of this mixin is to provide a metadata field on a model instance,
    for plugins to read / modify as required, to store any extra information.

    The assumptions for models implementing this mixin are:

    - The internal InvenTree business logic will make no use of this field
    - Multiple plugins may read / write to this metadata field, and not assume they have sole rights
    """

    class Meta:
        """Meta for MetadataMixin."""
        abstract = True

    metadata = models.JSONField(
        blank=True, null=True,
        verbose_name=_('Plugin Metadata'),
        help_text=_('JSON metadata field, for use by external plugins'),
    )

    def get_metadata(self, key: str, backup_value=None):
        """Finds metadata for this model instance, using the provided key for lookup.

        Args:
            key: String key for requesting metadata. e.g. if a plugin is accessing the metadata, the plugin slug should be used

        Returns:
            Python dict object containing requested metadata. If no matching metadata is found, returns None
        """
        if self.metadata is None:
            return backup_value

        return self.metadata.get(key, backup_value)

    def set_metadata(self, key: str, data, commit: bool = True):
        """Save the provided metadata under the provided key.

        Args:
            key (str): Key for saving metadata
            data (Any): Data object to save - must be able to be rendered as a JSON string
            commit (bool, optional): If true, existing metadata with the provided key will be overwritten. If false, a merge will be attempted. Defaults to True.
        """
        if self.metadata is None:
            # Handle a null field value
            self.metadata = {}

        self.metadata[key] = data

        if commit:
            self.save()


class PluginConfig(models.Model):
    """A PluginConfig object holds settings for plugins.

    Attributes:
        key: slug of the plugin (this must be unique across all installed plugins!)
        name: PluginName of the plugin - serves for a manual double check  if the right plugin is used
        active: Should the plugin be loaded?
    """

    class Meta:
        """Meta for PluginConfig."""
        verbose_name = _("Plugin Configuration")
        verbose_name_plural = _("Plugin Configurations")

    key = models.CharField(
        unique=True,
        max_length=255,
        verbose_name=_('Key'),
        help_text=_('Key of plugin'),
    )

    name = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('PluginName of the plugin'),
    )

    active = models.BooleanField(
        default=False,
        verbose_name=_('Active'),
        help_text=_('Is the plugin active'),
    )

    def __str__(self) -> str:
        """Nice name for printing."""
        name = f'{self.name} - {self.key}'
        if not self.active:
            name += '(not active)'
        return name

    # extra attributes from the registry
    def mixins(self):
        """Returns all registered mixins."""
        try:
            return self.plugin._mixinreg
        except (AttributeError, ValueError):  # pragma: no cover
            return {}

    # functions

    def __init__(self, *args, **kwargs):
        """Override to set original state of the plugin-config instance."""
        super().__init__(*args, **kwargs)
        self.__org_active = self.active

        # append settings from registry
        plugin = registry.plugins_full.get(self.key, None)

        def get_plugin_meta(name):
            if plugin:
                return str(getattr(plugin, name, None))
            return None

        self.meta = {
            key: get_plugin_meta(key) for key in ['slug', 'human_name', 'description', 'author',
                                                  'pub_date', 'version', 'website', 'license',
                                                  'package_path', 'settings_url', ]
        }

        # Save plugin
        self.plugin: InvenTreePlugin = plugin

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        """Extend save method to reload plugins if the 'active' status changes."""
        reload = kwargs.pop('no_reload', False)  # check if no_reload flag is set

        ret = super().save(force_insert, force_update, *args, **kwargs)

        if not reload:
            if (self.active is False and self.__org_active is True) or \
               (self.active is True and self.__org_active is False):
                if settings.PLUGIN_TESTING:
                    warnings.warn('A reload was triggered')
                registry.reload_plugins()

        return ret

    @admin.display(boolean=True, description=_('Sample plugin'))
    def is_sample(self) -> bool:
        """Is this plugin a sample app?"""
        # Loaded and active plugin
        if isinstance(self.plugin, InvenTreePlugin):
            return self.plugin.check_is_sample()

        # If no plugin_class is available it can not be a sample
        if not self.plugin:
            return False

        # Not loaded plugin
        return self.plugin.check_is_sample()  # pragma: no cover


class PluginSetting(common.models.BaseInvenTreeSetting):
    """This model represents settings for individual plugins."""

    typ = 'plugin'

    class Meta:
        """Meta for PluginSetting."""
        unique_together = [
            ('plugin', 'key'),
        ]

    plugin = models.ForeignKey(
        PluginConfig,
        related_name='settings',
        null=False,
        verbose_name=_('Plugin'),
        on_delete=models.CASCADE,
    )

    @classmethod
    def get_setting_definition(cls, key, **kwargs):
        """In the BaseInvenTreeSetting class, we have a class attribute named 'SETTINGS', which is a dict object that fully defines all the setting parameters.

        Here, unlike the BaseInvenTreeSetting, we do not know the definitions of all settings
        'ahead of time' (as they are defined externally in the plugins).

        Settings can be provided by the caller, as kwargs['settings'].

        If not provided, we'll look at the plugin registry to see what settings are available,
        (if the plugin is specified!)
        """
        if 'settings' not in kwargs:

            plugin = kwargs.pop('plugin', None)

            if plugin:

                if issubclass(plugin.__class__, InvenTreePlugin):
                    plugin = plugin.plugin_config()

                kwargs['settings'] = registry.mixins_settings.get(plugin.key, {})

        return super().get_setting_definition(key, **kwargs)

    def get_kwargs(self):
        """Explicit kwargs required to uniquely identify a particular setting object, in addition to the 'key' parameter."""
        return {
            'plugin': self.plugin,
        }


class NotificationUserSetting(common.models.BaseInvenTreeSetting):
    """This model represents notification settings for a user."""

    typ = 'notification'

    class Meta:
        """Meta for NotificationUserSetting."""
        unique_together = [
            ('method', 'user', 'key'),
        ]

    @classmethod
    def get_setting_definition(cls, key, **kwargs):
        """Override setting_definition to use notification settings."""
        from common.notifications import storage

        kwargs['settings'] = storage.user_settings

        return super().get_setting_definition(key, **kwargs)

    def get_kwargs(self):
        """Explicit kwargs required to uniquely identify a particular setting object, in addition to the 'key' parameter."""
        return {
            'method': self.method,
            'user': self.user,
        }

    method = models.CharField(
        max_length=255,
        verbose_name=_('Method'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True, null=True,
        verbose_name=_('User'),
        help_text=_('User'),
    )

    def __str__(self) -> str:
        """Nice name of printing."""
        return f'{self.key} (for {self.user}): {self.value}'
