"""
Plugin model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import gettext_lazy as _
from django.db import models

from plugin import plugin_reg


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

    def mixins(self):
        """
        Return the mixins associated with this plugin
        """

        if self.plugin:
            return self.plugin._mixinreg
        else:
            return {}

    def __init__(self, *args, **kwargs):
        """
        Override to set original state of the plugin-config instance
        """
        
        super().__init__(*args, **kwargs)
        self.__org_active = self.active

        # append settings from registry
        self.plugin = plugin_reg.plugins.get(self.key, None)

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
        """extend save method to reload plugins if the 'active' status changes"""
        reload = kwargs.pop('no_reload', False)  # check if no_reload flag is set

        ret = super().save(force_insert, force_update, *args, **kwargs)

        if not reload:
            if self.active is False and self.__org_active is True:
                plugin_reg.reload_plugins()

            elif self.active is True and self.__org_active is False:
                plugin_reg.reload_plugins()

        return ret
