# -*- coding: utf-8 -*-

""" This module provides template tags for handeling plugins
"""
from django.conf import settings as djangosettings
from django import template
from django.urls import reverse

from common.models import InvenTreeSetting


register = template.Library()


@register.simple_tag()
def plugin_list(*args, **kwargs):
    """ Return a list of all installed integration plugins """
    return djangosettings.INTEGRATION_PLUGINS


@register.simple_tag()
def inactive_plugin_list(*args, **kwargs):
    """ Return a list of all inactive integration plugins """
    return djangosettings.INTEGRATION_PLUGINS_INACTIVE


@register.simple_tag()
def plugin_settings(plugin, *args, **kwargs):
    """ Return a list of all settings for a plugin """
    return djangosettings.INTEGRATION_PLUGIN_SETTING.get(plugin)


@register.simple_tag()
def mixin_enabled(plugin, key, *args, **kwargs):
    """ Return if the mixin is existant and configured in the plugin """
    return plugin.mixin_enabled(key)


@register.simple_tag()
def navigation_enabled(*args, **kwargs):
    """Return if plugin navigation is enabled"""
    if djangosettings.TESTING:
        return True
    return InvenTreeSetting.get_setting('ENABLE_PLUGINS_NAVIGATION')


@register.simple_tag()
def safe_url(view_name, *args, **kwargs):
    """ safe lookup for urls """
    try:
        return reverse(view_name, args=args, kwargs=kwargs)
    except:
        return None
