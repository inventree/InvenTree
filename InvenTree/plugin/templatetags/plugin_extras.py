"""This module provides template tags for handeling plugins."""

from django import template
from django.conf import settings as djangosettings
from django.urls import reverse

from common.models import InvenTreeSetting
from common.notifications import storage
from plugin import registry

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
    """Is the mixin registerd and configured in the plugin?"""
    return plugin.mixin_enabled(key)


@register.simple_tag()
def mixin_available(mixin, *args, **kwargs):
    """Returns True if there is at least one active plugin which supports the provided mixin."""
    return len(registry.with_mixin(mixin)) > 0


@register.simple_tag()
def navigation_enabled(*args, **kwargs):
    """Is plugin navigation enabled?"""
    if djangosettings.PLUGIN_TESTING:
        return True
    return InvenTreeSetting.get_setting('ENABLE_PLUGINS_NAVIGATION')  # pragma: no cover


@register.simple_tag()
def safe_url(view_name, *args, **kwargs):
    """Safe lookup fnc for URLs.

    Returns None if not found
    """
    try:
        return reverse(view_name, args=args, kwargs=kwargs)
    except:
        return None


@register.simple_tag()
def plugin_errors(*args, **kwargs):
    """All plugin errors in the current session."""
    return registry.errors


@register.simple_tag(takes_context=True)
def notification_settings_list(context, *args, **kwargs):
    """List of all user notification settings."""
    return storage.get_usersettings(user=context.get('user', None))
