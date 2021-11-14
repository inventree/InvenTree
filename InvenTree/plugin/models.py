"""
Plugin model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import gettext_lazy as _
from django.db import models
from django.apps import apps


class PluginConfig(models.Model):
    """ A PluginConfig object holds settings for plugins.

    It is used to designate a Part as 'subscribed' for a given User.

    Attributes:
        key: slug of the plugin - must be unique
        name: PluginName of the plugin - serves for a manual double check  if the right plugin is used
        active: Should the plugin be loaded?
    """

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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__org_active = self.active

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        """extend save method to reload plugins if the 'active' status changes"""
        ret = super().save(force_insert, force_update,  *args, **kwargs)
        app = apps.get_app_config('plugin')

        if self.active is False and self.__org_active is True:
            print('deactivated')
            app.reload_plugins()

        elif self.active is True and self.__org_active is False:
            print('activated')
            app.reload_plugins()

        return ret

