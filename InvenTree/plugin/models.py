"""
Plugin model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import gettext_lazy as _
from django.db import models


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
