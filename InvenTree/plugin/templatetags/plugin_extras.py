# -*- coding: utf-8 -*-

""" This module provides template tags for handeling plugins
"""
from django.conf import settings as djangosettings
from django import template
from django.urls import reverse

from common.models import InvenTreeSetting
from plugin import plugin_reg


register = template.Library()


@register.simple_tag()
def plugin_list(*args, **kwargs):
    """ Return a list of all installed integration plugins """
    return plugin_reg.plugins


@register.simple_tag()
def inactive_plugin_list(*args, **kwargs):
    """ Return a list of all inactive integration plugins """
    return plugin_reg.plugins_inactive


@register.simple_tag()
def plugin_globalsettings(plugin, *args, **kwargs):
    """ Return a list of all global settings for a plugin """
    return plugin_reg.mixins_globalsettings.get(plugin)


@register.simple_tag()
def mixin_enabled(plugin, key, *args, **kwargs):
    """ Return if the mixin is existant and configured in the plugin """
    return plugin.mixin_enabled(key)


@register.simple_tag()
def navigation_enabled(*args, **kwargs):
    """Return if plugin navigation is enabled"""
    if djangosettings.PLUGIN_TESTING:
        return True
    return InvenTreeSetting.get_setting('ENABLE_PLUGINS_NAVIGATION')


@register.simple_tag()
def safe_url(view_name, *args, **kwargs):
    """ safe lookup for urls """
    try:
        return reverse(view_name, args=args, kwargs=kwargs)
    except:
        return None


@register.simple_tag()
def plugin_errors(*args, **kwargs):
    """Return all plugin errors"""
    return plugin_reg.errors
