"""
Plugin model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth.models import User

import common.models

from plugin import InvenTreePlugin, registry


class PluginConfig(models.Model):
    """
    A PluginConfig object holds settings for plugins.

    Attributes:
        key: slug of the plugin (this must be unique across all installed plugins!)
        name: PluginName of the plugin - serves for a manual double check  if the right plugin is used
        active: Should the plugin be loaded?
    """
    class Meta:
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
        name = f'{self.name} - {self.key}'
        if not self.active:
            name += '(not active)'
        return name

    # extra attributes from the registry
    def mixins(self):

        try:
            return self.plugin._mixinreg
        except (AttributeError, ValueError):  # pragma: no cover
            return {}

    # functions

    def __init__(self, *args, **kwargs):
        """
        Override to set original state of the plugin-config instance
        """

        super().__init__(*args, **kwargs)
        self.__org_active = self.active

        # append settings from registry
        self.plugin = registry.plugins.get(self.key, None)

        def get_plugin_meta(name):
            if self.plugin:
                return str(getattr(self.plugin, name, None))
            return None

        self.meta = {
            key: get_plugin_meta(key) for key in ['slug', 'human_name', 'description', 'author',
                                                  'pub_date', 'version', 'website', 'license',
                                                  'package_path', 'settings_url', ]
        }

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        """
        Extend save method to reload plugins if the 'active' status changes
        """
        reload = kwargs.pop('no_reload', False)  # check if no_reload flag is set

        ret = super().save(force_insert, force_update, *args, **kwargs)

        if not reload:
            if (self.active is False and self.__org_active is True) or \
               (self.active is True and self.__org_active is False):
                registry.reload_plugins()

        return ret


class PluginSetting(common.models.GenericReferencedSettingClass, common.models.BaseInvenTreeSetting):
    """
    This model represents settings for individual plugins
    """

    class Meta:
        unique_together = [
            ('plugin', 'key'),
        ]

    REFERENCE_NAME = 'plugin'

    @classmethod
    def get_setting_definition(cls, key, **kwargs):
        """
        In the BaseInvenTreeSetting class, we have a class attribute named 'SETTINGS',
        which is a dict object that fully defines all the setting parameters.

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

    plugin = models.ForeignKey(
        PluginConfig,
        related_name='settings',
        null=False,
        verbose_name=_('Plugin'),
        on_delete=models.CASCADE,
    )


class NotificationUserSetting(common.models.GenericReferencedSettingClass, common.models.BaseInvenTreeSetting):
    """
    This model represents notification settings for a user
    """

    class Meta:
        unique_together = [
            ('method', 'user', 'key'),
        ]

    REFERENCE_NAME = 'method'

    @classmethod
    def get_setting_definition(cls, key, **kwargs):
        from common.notifications import storage

        kwargs['settings'] = storage.user_settings

        return super().get_setting_definition(key, **kwargs)

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
        return f'{self.key} (for {self.user}): {self.value}'
