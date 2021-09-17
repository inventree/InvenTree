# -*- coding: utf-8 -*-

""" This module provides template tags for handeling plugins
"""
from django.conf import settings as djangosettings
from django import template


register = template.Library()


@register.simple_tag()
def plugin_list(*args, **kwargs):
    """ Return a list of all installed integration plugins """
    return djangosettings.INTEGRATION_PLUGIN_LIST


@register.simple_tag()
def plugin_settings(plugin, *args, **kwargs):
    """ Return a list of all settings for a plugin """
    return djangosettings.INTEGRATION_PLUGIN_SETTING.get(plugin)
