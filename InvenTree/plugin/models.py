"""Plugin model definitions."""

import inspect
import warnings

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _

import common.models
import InvenTree.models
from plugin import InvenTreePlugin, registry


class PluginConfig(InvenTree.models.MetadataMixin, models.Model):
    """A PluginConfig object holds settings for plugins.

    Attributes:
        key: slug of the plugin (this must be unique across all installed plugins!)
        name: PluginName of the plugin - serves for a manual double check  if the right plugin is used
        active: Should the plugin be loaded?
    """

    class Meta:
        """Meta for PluginConfig."""

        verbose_name = _('Plugin Configuration')
        verbose_name_plural = _('Plugin Configurations')

    key = models.CharField(
        unique=True, max_length=255, verbose_name=_('Key'), help_text=_('Key of plugin')
    )

    name = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('PluginName of the plugin'),
    )

    package_name = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name=_('Package Name'),
        help_text=_(
            'Name of the installed package, if the plugin was installed via PIP'
        ),
    )

    active = models.BooleanField(
        default=False, verbose_name=_('Active'), help_text=_('Is the plugin active')
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
            if inspect.isclass(self.plugin):
                return self.plugin.get_registered_mixins(
                    self, with_base=True, with_cls=False
                )
            return self.plugin.get_registered_mixins(with_base=True, with_cls=False)
        except (AttributeError, ValueError):  # pragma: no cover
            return {}

    # functions

    def __init__(self, *args, **kwargs):
        """Override to set original state of the plugin-config instance."""
        super().__init__(*args, **kwargs)
        self.__org_active = self.active

        # Append settings from registry
        plugin = registry.plugins_full.get(self.key, None)

        def get_plugin_meta(name):
            """Return a meta-value associated with this plugin."""
            # Ignore if the plugin config is not defined
            if not plugin:
                return None

            # Ignore if the plugin is not active
            if not self.active:
                return None

            result = getattr(plugin, name, None)

            if result is not None:
                result = str(result)

            return result

        self.meta = {
            key: get_plugin_meta(key)
            for key in [
                'slug',
                'human_name',
                'description',
                'author',
                'pub_date',
                'version',
                'website',
                'license',
                'package_path',
                'settings_url',
            ]
        }

        # Save plugin
        self.plugin: InvenTreePlugin = plugin

    def __getstate__(self):
        """Customize pickling behavior."""
        state = super().__getstate__()
        state.pop(
            'plugin', None
        )  # plugin cannot be pickled in some circumstances when used with drf views, remove it (#5408)
        return state

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        """Extend save method to reload plugins if the 'active' status changes."""
        reload = kwargs.pop('no_reload', False)  # check if no_reload flag is set

        super().save(force_insert, force_update, *args, **kwargs)

        if self.is_builtin():
            # Force active if builtin
            self.active = True

        if not reload:
            if self.active != self.__org_active:
                if settings.PLUGIN_TESTING:
                    warnings.warn('A reload was triggered', stacklevel=2)
                registry.reload_plugins()

    @admin.display(boolean=True, description=_('Installed'))
    def is_installed(self) -> bool:
        """Simple check to determine if this plugin is installed.

        A plugin might not be installed if it has been removed from the system,
        but the PluginConfig associated with it still exists.
        """
        return self.plugin is not None

    @admin.display(boolean=True, description=_('Sample plugin'))
    def is_sample(self) -> bool:
        """Is this plugin a sample app?"""
        if not self.plugin:
            return False

        return self.plugin.check_is_sample()

    @admin.display(boolean=True, description=_('Builtin Plugin'))
    def is_builtin(self) -> bool:
        """Return True if this is a 'builtin' plugin."""
        if not self.plugin:
            return False

        return self.plugin.check_is_builtin()

    @admin.display(boolean=True, description=_('Package Plugin'))
    def is_package(self) -> bool:
        """Return True if this is a 'package' plugin."""
        if not self.plugin:
            return False

        return getattr(self.plugin, 'is_package', False)


class PluginSetting(common.models.BaseInvenTreeSetting):
    """This model represents settings for individual plugins."""

    typ = 'plugin'
    extra_unique_fields = ['plugin']

    class Meta:
        """Meta for PluginSetting."""

        unique_together = [('plugin', 'key')]

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
                mixin_settings = getattr(registry, 'mixins_settings', None)
                if mixin_settings:
                    kwargs['settings'] = mixin_settings.get(plugin.key, {})

        return super().get_setting_definition(key, **kwargs)


class NotificationUserSetting(common.models.BaseInvenTreeSetting):
    """This model represents notification settings for a user."""

    typ = 'notification'
    extra_unique_fields = ['method', 'user']

    class Meta:
        """Meta for NotificationUserSetting."""

        unique_together = [('method', 'user', 'key')]

    @classmethod
    def get_setting_definition(cls, key, **kwargs):
        """Override setting_definition to use notification settings."""
        from common.notifications import storage

        kwargs['settings'] = storage.user_settings

        return super().get_setting_definition(key, **kwargs)

    method = models.CharField(max_length=255, verbose_name=_('Method'))

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('User'),
        help_text=_('User'),
    )

    def __str__(self) -> str:
        """Nice name of printing."""
        return f'{self.key} (for {self.user}): {self.value}'
