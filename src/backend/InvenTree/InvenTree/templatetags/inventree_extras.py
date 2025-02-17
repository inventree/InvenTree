"""This module provides template tags for extra functionality, over and above the built-in Django tags."""

from datetime import date, datetime

from django import template
from django.conf import settings as djangosettings

import structlog

import common.models
import InvenTree.helpers
import InvenTree.helpers_model
import plugin.models
from common.settings import get_global_setting
from InvenTree import version
from plugin.plugin import InvenTreePlugin

register = template.Library()


logger = structlog.get_logger('inventree')


@register.simple_tag()
def define(value, *args, **kwargs):
    """Shortcut function to overcome the shortcomings of the django templating language.

    Use as follows: {% define "hello_world" as hello %}

    Ref: https://stackoverflow.com/questions/1070398/how-to-set-a-value-of-a-variable-inside-a-template-code
    """
    return value


@register.simple_tag()
def decimal(x, *args, **kwargs):
    """Simplified rendering of a decimal number."""
    return InvenTree.helpers.decimal2string(x)


@register.simple_tag(takes_context=True)
def render_date(date_object):
    """Renders a date object as a string."""
    if date_object is None:
        return None

    if isinstance(date_object, str):
        date_object = date_object.strip()

        # Check for empty string
        if len(date_object) == 0:
            return None

        # If a string is passed, first convert it to a datetime
        try:
            date_object = date.fromisoformat(date_object)
        except ValueError:
            logger.warning('Tried to convert invalid date string: %s', date_object)
            return None

    user_date_format = '%Y-%m-%d'
    if isinstance(date_object, (datetime, date)):
        return date_object.strftime(user_date_format)
    return date_object


@register.simple_tag()
def str2bool(x, *args, **kwargs):
    """Convert a string to a boolean value."""
    return InvenTree.helpers.str2bool(x)


@register.simple_tag()
def add(x, y, *args, **kwargs):
    """Add two numbers together."""
    return x + y


@register.simple_tag()
def to_list(*args):
    """Return the input arguments as list."""
    return args


@register.simple_tag()
def inventree_instance_name(*args, **kwargs):
    """Return the InstanceName associated with the current database."""
    return version.inventreeInstanceName()


@register.simple_tag()
def inventree_title(*args, **kwargs):
    """Return the title for the current instance - respecting the settings."""
    return version.inventreeInstanceTitle()


@register.simple_tag()
def inventree_logo(**kwargs):
    """Return the InvenTree logo, *or* a custom logo if the user has provided one.

    Returns a path to an image file, which can be rendered in the web interface.
    """
    return InvenTree.helpers.getLogoImage(**kwargs)


@register.simple_tag()
def inventree_version(shortstring=False, *args, **kwargs):
    """Return InvenTree version string."""
    if shortstring:
        return f'{version.inventreeInstanceTitle()} v{version.inventreeVersion()}'
    return version.inventreeVersion()


@register.simple_tag()
def inventree_commit_hash(*args, **kwargs):
    """Return InvenTree git commit hash string."""
    return version.inventreeCommitHash()


@register.simple_tag()
def inventree_installer(*args, **kwargs):
    """Return InvenTree package installer string."""
    return version.inventreeInstaller()


@register.simple_tag()
def inventree_commit_date(*args, **kwargs):
    """Return InvenTree git commit date string."""
    return version.inventreeCommitDate()


@register.simple_tag()
def setting_object(key, *args, **kwargs):
    """Return a setting object specified by the given key.

    (Or return None if the setting does not exist)
    if a user-setting was requested return that
    """
    cache = kwargs.get('cache', True)

    if 'plugin' in kwargs:
        # Note, 'plugin' is an instance of an InvenTreePlugin class

        plg = kwargs['plugin']
        if issubclass(plg.__class__, InvenTreePlugin):
            try:
                plg = plg.plugin_config()
            except plugin.models.PluginConfig.DoesNotExist:
                return None

        return plugin.models.PluginSetting.get_setting_object(
            key, plugin=plg, cache=cache
        )

    elif 'method' in kwargs:
        return plugin.models.NotificationUserSetting.get_setting_object(
            key, user=kwargs['user'], method=kwargs['method'], cache=cache
        )

    elif 'user' in kwargs:
        return common.models.InvenTreeUserSetting.get_setting_object(
            key, user=kwargs['user'], cache=cache
        )

    else:
        return common.models.InvenTreeSetting.get_setting_object(key, cache=cache)


@register.simple_tag()
def settings_value(key, *args, **kwargs):
    """Return a settings value specified by the given key."""
    if 'user' in kwargs:
        if not kwargs['user'] or (
            kwargs['user'] and kwargs['user'].is_authenticated is False
        ):
            return common.models.InvenTreeUserSetting.get_setting(key)
        return common.models.InvenTreeUserSetting.get_setting(key, user=kwargs['user'])

    return get_global_setting(key)


@register.filter
def keyvalue(dict, key):
    """Access to key of supplied dict.

    Usage:
    {% mydict|keyvalue:mykey %}
    """
    return dict.get(key)


@register.simple_tag()
def inventree_customize(reference, *args, **kwargs):
    """Return customization values for the user interface."""
    return djangosettings.CUSTOMIZE.get(reference, '')
