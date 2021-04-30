""" This module provides template tags for extra functionality
over and above the built-in Django tags.
"""
import os

from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.templatetags.static import StaticNode
from InvenTree import version, settings

import InvenTree.helpers

from common.models import InvenTreeSetting, ColorTheme

register = template.Library()


@register.simple_tag()
def define(value, *args, **kwargs):
    """
    Shortcut function to overcome the shortcomings of the django templating language

    Use as follows: {% define "hello_world" as hello %}

    Ref: https://stackoverflow.com/questions/1070398/how-to-set-a-value-of-a-variable-inside-a-template-code
    """

    return value


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
    return InvenTree.helpers.decimal2string(x * y)


@register.simple_tag()
def add(x, y, *args, **kwargs):
    """ Add two numbers together """
    return x + y
    

@register.simple_tag()
def part_allocation_count(build, part, *args, **kwargs):
    """ Return the total number of <part> allocated to <build> """

    return InvenTree.helpers.decimal2string(build.getAllocatedQuantity(part))


@register.simple_tag()
def inventree_instance_name(*args, **kwargs):
    """ Return the InstanceName associated with the current database """
    return version.inventreeInstanceName()


@register.simple_tag()
def inventree_title(*args, **kwargs):
    """ Return the title for the current instance - respecting the settings """
    return version.inventreeInstanceTitle()


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
def inventree_credits_url(*args, **kwargs):
    """ Return URL for InvenTree credits site """
    return "https://inventree.readthedocs.io/en/latest/credits/"


@register.simple_tag()
def setting_object(key, *args, **kwargs):
    """
    Return a setting object speciifed by the given key
    (Or return None if the setting does not exist)
    """

    setting = InvenTreeSetting.get_setting_object(key)

    return setting


@register.simple_tag()
def settings_value(key, *args, **kwargs):
    """
    Return a settings value specified by the given key
    """

    return InvenTreeSetting.get_setting(key)


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


@register.simple_tag()
def authorized_owners(group):
    """ Return authorized owners """

    owners = []

    try:
        for owner in group.get_related_owners(include_group=True):
            owners.append(owner.owner)
    except AttributeError:
        # group is None
        pass
    except TypeError:
        # group.get_users returns None
        pass
    
    return owners


@register.simple_tag()
def object_link(url_name, pk, ref):
    """ Return highlighted link to object """

    ref_url = reverse(url_name, kwargs={'pk': pk})
    return mark_safe('<b><a href="{}">{}</a></b>'.format(ref_url, ref))


class I18nStaticNode(StaticNode):
    """
    custom StaticNode
    replaces a variable named *lng* in the path with the current language
    """
    def render(self, context):
        self.path.var = self.path.var.format(lng=context.request.LANGUAGE_CODE)
        ret = super().render(context)
        return ret


@register.tag('i18n_static')
def do_i18n_static(parser, token):
    """
    Overrides normal static, adds language - lookup for prerenderd files #1485

    usage (like static):
    {% i18n_static path [as varname] %}
    """
    bits = token.split_contents()
    loc_name = settings.STATICFILES_I18_PREFIX

    # change path to called ressource
    bits[1] = f"'{loc_name}/{{lng}}.{bits[1][1:-1]}'"
    token.contents = ' '.join(bits)
    return I18nStaticNode.handle_token(parser, token)
