"""This module provides template tags for handling plugins."""

from django import template
from django.urls import reverse

from plugin.registry import registry

register = template.Library()


@register.simple_tag()
def plugin_list(*args, **kwargs):
    """List of all installed plugins."""
    return registry.plugins


@register.simple_tag()
def inactive_plugin_list(*args, **kwargs):
    """List of all inactive plugins."""
    return registry.plugins_inactive


@register.simple_tag()
def plugin_settings(plugin, *args, **kwargs):
    """List of all settings for the plugin."""
    return registry.mixins_settings.get(plugin)


@register.simple_tag()
def mixin_enabled(plugin, key, *args, **kwargs):
    """Is the mixin registered and configured in the plugin?"""
    return plugin.mixin_enabled(key)


@register.simple_tag()
def mixin_available(mixin, *args, **kwargs):
    """Returns True if there is at least one active plugin which supports the provided mixin."""
    return len(registry.with_mixin(mixin)) > 0


@register.simple_tag()
def safe_url(view_name, *args, **kwargs):
    """Safe lookup fnc for URLs.

    Returns None if not found
    """
    try:
        return reverse(view_name, args=args, kwargs=kwargs)
    except Exception:
        return None
