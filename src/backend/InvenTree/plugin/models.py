"""Plugin model definitions."""

import inspect
import warnings
from typing import Optional

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import common.models
import InvenTree.models
import plugin.staticfiles
from plugin import InvenTreePlugin
from plugin.events import PluginEvents, trigger_event
from plugin.registry import registry


class PluginConfig(InvenTree.models.MetadataMixin, models.Model):
    """A PluginConfig object holds settings for plugins.

    Attributes:
        key: slug of the plugin (this must be unique across all installed plugins!)
        name: Name of the plugin - serves for a manual double check  if the right plugin is used
        active: Should the plugin be loaded?
    """

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the PluginConfig model."""
        return reverse('api-plugin-list')

    class Meta:
        """Meta for PluginConfig."""

        verbose_name = _('Plugin Configuration')
        verbose_name_plural = _('Plugin Configurations')

    key = models.CharField(
        unique=True,
        db_index=True,
        max_length=255,
        verbose_name=_('Key'),
        help_text=_('Key of plugin'),
    )

    name = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('Name of the plugin'),
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
            name += ' (not active)'
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
        no_reload = kwargs.pop('no_reload', False)  # check if no_reload flag is set

        mandatory = self.is_mandatory()

        if mandatory:
            # Force active if mandatory plugin
            self.active = True

        super().save(force_insert, force_update, *args, **kwargs)

        if not no_reload and self.active != self.__org_active and not mandatory:
            if settings.PLUGIN_TESTING:
                warnings.warn(
                    f'A plugin registry reload was triggered for plugin {self.key}',
                    stacklevel=2,
                )
            registry.reload_plugins(full_reload=True, force_reload=True, collect=True)

        self.__org_active = self.active

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

    @admin.display(boolean=True, description=_('Mandatory Plugin'))
    def is_mandatory(self) -> bool:
        """Return True if this plugin is mandatory."""
        # List of run-time configured mandatory plugins
        if settings.PLUGINS_MANDATORY:
            if self.key in settings.PLUGINS_MANDATORY:
                return True

        # Hard-coded list of mandatory "builtin" plugins
        return self.key in registry.MANDATORY_PLUGINS

    def is_active(self) -> bool:
        """Return True if this plugin is active.

        Note that 'mandatory' plugins are always considered 'active',
        """
        return self.is_mandatory() or self.active

    @admin.display(boolean=True, description=_('Package Plugin'))
    def is_package(self) -> bool:
        """Return True if this is a 'package' plugin."""
        if self.package_name:
            return True

        if not self.plugin:
            return False

        pkg_name = getattr(self.plugin, 'package_name', None)
        return pkg_name is not None

    @property
    def admin_source(self) -> Optional[str]:
        """Return the path to the javascript file which renders custom admin content for this plugin.

        - It is required that the file provides a 'renderPluginSettings' function!
        """
        if not self.plugin:
            return None

        if not self.is_installed() or not self.active:
            return None

        if hasattr(self.plugin, 'get_admin_source'):
            try:
                return self.plugin.get_admin_source()
            except Exception:
                pass

        return None

    @property
    def admin_context(self) -> Optional[dict]:
        """Return the context data for the admin integration."""
        if not self.plugin:
            return None

        if not self.is_installed() or not self.active:
            return None

        if hasattr(self.plugin, 'get_admin_context'):
            try:
                return self.plugin.get_admin_context()
            except Exception:
                pass

        return {}

    def activate(self, active: bool) -> None:
        """Set the 'active' status of this plugin instance."""
        from InvenTree.tasks import check_for_migrations, offload_task

        if self.active == active:
            return

        self.active = active
        self.save()

        trigger_event(PluginEvents.PLUGIN_ACTIVATED, slug=self.key, active=active)

        if active:
            offload_task(check_for_migrations)
            offload_task(
                plugin.staticfiles.copy_plugin_static_files, self.key, group='plugin'
            )
        else:
            offload_task(
                plugin.staticfiles.clear_plugin_static_files, self.key, group='plugin'
            )


class PluginSetting(common.models.BaseInvenTreeSetting):
    """This model represents settings for individual plugins."""

    typ = 'plugin'
    extra_unique_fields = ['plugin']

    class Meta:
        """Meta for PluginSetting."""

        unique_together = [('plugin', 'key')]

    def to_native_value(self):
        """Return the 'native' value of this setting."""
        return self.__class__.get_setting(self.key, plugin=self.plugin)

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


class PluginUserSetting(common.models.BaseInvenTreeSetting):
    """This model represents user-specific settings for individual plugins.

    In contrast with the PluginSetting model, which holds global settings for plugins,
    this model allows for user-specific settings that can be defined by each user.
    """

    typ = 'plugin_user'
    extra_unique_fields = ['plugin', 'user']

    class Meta:
        """Meta for PluginUserSetting."""

        unique_together = [('plugin', 'user', 'key')]

    plugin = models.ForeignKey(
        PluginConfig,
        related_name='user_settings',
        null=False,
        verbose_name=_('Plugin'),
        on_delete=models.CASCADE,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        verbose_name=_('User'),
        help_text=_('User'),
        related_name='plugin_settings',
    )

    def __str__(self) -> str:
        """Nice name of printing."""
        return f'{self.key} (for {self.user}): {self.value}'

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
                mixin_user_settings = getattr(registry, 'mixins_user_settings', None)
                if mixin_user_settings:
                    kwargs['settings'] = mixin_user_settings.get(plugin.key, {})

        return super().get_setting_definition(key, **kwargs)
