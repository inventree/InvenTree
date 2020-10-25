""" This module provides template tags for extra functionality
over and above the built-in Django tags.
"""
import os

from django import template
from InvenTree import version, settings

import InvenTree.helpers

from common.models import InvenTreeSetting, ColorTheme

register = template.Library()


@register.simple_tag()
def decimal(x, *args, **kwargs):
    """ Simplified rendering of a decimal number """

    return InvenTree.helpers.decimal2string(x)


@register.simple_tag()
def str2bool(x, *args, **kwargs):
    """ Convert a string to a boolean value """

    return InvenTree.helpers.str2bool(x)

@register.simple_tag()
def inrange(n, *args, **kwargs):
    """ Return range(n) for iterating through a numeric quantity """
    return range(n)
    

@register.simple_tag()
def multiply(x, y, *args, **kwargs):
    """ Multiply two numbers together """
    return decimal2string(x * y)


@register.simple_tag()
def add(x, y, *args, **kwargs):
    """ Add two numbers together """
    return x + y
    

@register.simple_tag()
def part_allocation_count(build, part, *args, **kwargs):
    """ Return the total number of <part> allocated to <build> """

    return decimal2string(build.getAllocatedQuantity(part))


@register.simple_tag()
def inventree_instance_name(*args, **kwargs):
    """ Return the InstanceName associated with the current database """
    return version.inventreeInstanceName()


@register.simple_tag()
def inventree_version(*args, **kwargs):
    """ Return InvenTree version string """
    return version.inventreeVersion()


@register.simple_tag()
def django_version(*args, **kwargs):
    """ Return Django version string """
    return version.inventreeDjangoVersion()


@register.simple_tag()
def inventree_commit_hash(*args, **kwargs):
    """ Return InvenTree git commit hash string """
    return version.inventreeCommitHash()


@register.simple_tag()
def inventree_commit_date(*args, **kwargs):
    """ Return InvenTree git commit date string """
    return version.inventreeCommitDate()


@register.simple_tag()
def inventree_github_url(*args, **kwargs):
    """ Return URL for InvenTree github site """
    return "https://github.com/InvenTree/InvenTree/"


@register.simple_tag()
def inventree_docs_url(*args, **kwargs):
    """ Return URL for InvenTree documenation site """
    return "https://inventree.readthedocs.io/"


@register.simple_tag()
def setting_object(key, *args, **kwargs):
    """
    Return a setting object speciifed by the given key
    (Or return None if the setting does not exist)
    """

    setting = InvenTreeSetting.get_setting_object(key)

    print("Setting:", key, setting)

    return setting

@register.simple_tag()
def settings_name(key, *args, **kwargs):
    """
    Returns the name of a GLOBAL_SETTINGS object
    """

    return InvenTreeSetting.get_setting_name(key)


@register.simple_tag()
def settings_description(key, *args, **kwargs):
    """
    Returns the description of a GLOBAL_SETTINGS object
    """

    return InvenTreeSetting.get_setting_description(key)


@register.simple_tag()
def settings_units(key, *args, **kwargs):
    """
    Return the units of a GLOBAL_SETTINGS object
    """

    return InvenTreeSetting.get_setting_units(key)


@register.simple_tag()
def settings_value(key, *args, **kwargs):
    """
    Returns the value of a GLOBAL_SETTINGS object
    """

    return InvenTreeSetting.get_setting(key, backup_value=kwargs.get('backup', None))


@register.simple_tag()
def settings_pk(key, *args, **kwargs):
    """
    Return the ID (pk) of a GLOBAL_SETTINGS Object
    """

    return InvenTreeSetting.get_setting_pk(key)


@register.simple_tag()
def get_color_theme_css(username):
    try:
        user_theme = ColorTheme.objects.filter(user=username).get()
        user_theme_name = user_theme.name
        if not user_theme_name or not ColorTheme.is_valid_choice(user_theme):
            user_theme_name = 'default'
    except ColorTheme.DoesNotExist:
        user_theme_name = 'default'

    # Build path to CSS sheet
    inventree_css_sheet = os.path.join('css', 'color-themes', user_theme_name + '.css')

    # Build static URL
    inventree_css_static_url = os.path.join(settings.STATIC_URL, inventree_css_sheet)

    return inventree_css_static_url
