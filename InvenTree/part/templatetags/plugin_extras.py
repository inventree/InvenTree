# -*- coding: utf-8 -*-

""" This module provides template tags for handeling plugins
"""
from django.conf import settings as djangosettings
from django import template


register = template.Library()


@register.simple_tag()
def plugin_list(*args, **kwargs):
    """ Return a list of all installed integration plugins """
    return djangosettings.INTEGRATION_PLUGINS


@register.simple_tag()
def plugin_settings(plugin, *args, **kwargs):
    """ Return a list of all settings for a plugin """
    return djangosettings.INTEGRATION_PLUGIN_SETTING.get(plugin)


@register.simple_tag()
def mixin_enabled(plugin, key, *args, **kwargs):
    """ Return if the mixin is existant and configured in the plugin """
    return plugin.mixin_enabled(key)
