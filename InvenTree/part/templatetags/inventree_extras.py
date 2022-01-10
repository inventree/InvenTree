# -*- coding: utf-8 -*-

"""
This module provides template tags for extra functionality,
over and above the built-in Django tags.
"""

import os
import sys
from django.utils.html import format_html

from django.utils.translation import ugettext_lazy as _
from django.conf import settings as djangosettings

from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.templatetags.static import StaticNode
from InvenTree import version, settings

import InvenTree.helpers

from common.models import InvenTreeSetting, ColorTheme, InvenTreeUserSetting
from common.settings import currency_code_default

from plugin.models import PluginSetting

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
def to_list(*args):
    """ Return the input arguments as list """
    return args


@register.simple_tag()
def part_allocation_count(build, part, *args, **kwargs):
    """ Return the total number of <part> allocated to <build> """

    return InvenTree.helpers.decimal2string(build.getAllocatedQuantity(part))


@register.simple_tag()
def inventree_in_debug_mode(*args, **kwargs):
    """ Return True if the server is running in DEBUG mode """

    return djangosettings.DEBUG


@register.simple_tag()
def inventree_demo_mode(*args, **kwargs):
    """ Return True if the server is running in DEMO mode """

    return djangosettings.DEMO_MODE


@register.simple_tag()
def inventree_docker_mode(*args, **kwargs):
    """ Return True if the server is running as a Docker image """

    return djangosettings.DOCKER


@register.simple_tag()
def inventree_db_engine(*args, **kwargs):
    """ Return the InvenTree database backend e.g. 'postgresql' """

    db = djangosettings.DATABASES['default']

    engine = db.get('ENGINE', _('Unknown database'))

    engine = engine.replace('django.db.backends.', '')

    return engine


@register.simple_tag()
def inventree_instance_name(*args, **kwargs):
    """ Return the InstanceName associated with the current database """
    return version.inventreeInstanceName()


@register.simple_tag()
def inventree_title(*args, **kwargs):
    """ Return the title for the current instance - respecting the settings """
    return version.inventreeInstanceTitle()


@register.simple_tag()
def inventree_base_url(*args, **kwargs):
    """ Return the INVENTREE_BASE_URL setting """
    return InvenTreeSetting.get_setting('INVENTREE_BASE_URL')


@register.simple_tag()
def python_version(*args, **kwargs):
    """
    Return the current python version
    """
    return sys.version.split(' ')[0]


@register.simple_tag()
def inventree_version(*args, **kwargs):
    """ Return InvenTree version string """
    return version.inventreeVersion()


@register.simple_tag()
def inventree_is_development(*args, **kwargs):
    return version.isInvenTreeDevelopmentVersion()


@register.simple_tag()
def inventree_is_release(*args, **kwargs):
    return not version.isInvenTreeDevelopmentVersion()


@register.simple_tag()
def inventree_docs_version(*args, **kwargs):
    return version.inventreeDocsVersion()


@register.simple_tag()
def inventree_api_version(*args, **kwargs):
    """ Return InvenTree API version """
    return version.inventreeApiVersion()


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

    tag = version.inventreeDocsVersion()

    return f"https://inventree.readthedocs.io/en/{tag}"


@register.simple_tag()
def inventree_credits_url(*args, **kwargs):
    """ Return URL for InvenTree credits site """
    return "https://inventree.readthedocs.io/en/latest/credits/"


@register.simple_tag()
def default_currency(*args, **kwargs):
    """ Returns the default currency code """
    return currency_code_default()


@register.simple_tag()
def setting_object(key, *args, **kwargs):
    """
    Return a setting object speciifed by the given key
    (Or return None if the setting does not exist)
    if a user-setting was requested return that
    """

    if 'plugin' in kwargs:
        # Note, 'plugin' is an instance of an InvenTreePlugin class

        plugin = kwargs['plugin']

        return PluginSetting.get_setting_object(key, plugin=plugin)

    if 'user' in kwargs:
        return InvenTreeUserSetting.get_setting_object(key, user=kwargs['user'])

    return InvenTreeSetting.get_setting_object(key)


@register.simple_tag()
def settings_value(key, *args, **kwargs):
    """
    Return a settings value specified by the given key
    """

    if 'user' in kwargs:
        return InvenTreeUserSetting.get_setting(key, user=kwargs['user'])

    return InvenTreeSetting.get_setting(key)


@register.simple_tag()
def user_settings(user, *args, **kwargs):
    """
    Return all USER settings as a key:value dict
    """

    return InvenTreeUserSetting.allValues(user=user)


@register.simple_tag()
def global_settings(*args, **kwargs):
    """
    Return all GLOBAL InvenTree settings as a key:value dict
    """

    return InvenTreeSetting.allValues()


@register.simple_tag()
def visible_global_settings(*args, **kwargs):
    """
    Return any global settings which are not marked as 'hidden'
    """

    return InvenTreeSetting.allValues(exclude_hidden=True)


@register.simple_tag()
def progress_bar(val, max, *args, **kwargs):
    """
    Render a progress bar element
    """

    id = kwargs.get('id', 'progress-bar')

    if val > max:
        style = 'progress-bar-over'
    elif val < max:
        style = 'progress-bar-under'
    else:
        style = ''

    percent = float(val / max) * 100

    if percent > 100:
        percent = 100
    elif percent < 0:
        percent = 0

    style_tags = []

    max_width = kwargs.get('max_width', None)

    if max_width:
        style_tags.append(f'max-width: {max_width};')

    html = f"""
    <div id='{id}' class='progress' style='{" ".join(style_tags)}'>
        <div class='progress-bar {style}' role='progressbar' aria-valuemin='0' aria-valuemax='100' style='width:{percent}%'></div>
        <div class='progress-value'>{val} / {max}</div>
    </div>
    """

    return mark_safe(html)


@register.simple_tag()
def get_color_theme_css(username):
    user_theme_name = get_user_color_theme(username)
    # Build path to CSS sheet
    inventree_css_sheet = os.path.join('css', 'color-themes', user_theme_name + '.css')

    # Build static URL
    inventree_css_static_url = os.path.join(settings.STATIC_URL, inventree_css_sheet)

    return inventree_css_static_url


@register.simple_tag()
def get_user_color_theme(username):
    """ Get current user color theme """
    try:
        user_theme = ColorTheme.objects.filter(user=username).get()
        user_theme_name = user_theme.name
        if not user_theme_name or not ColorTheme.is_valid_choice(user_theme):
            user_theme_name = 'default'
    except ColorTheme.DoesNotExist:
        user_theme_name = 'default'

    return user_theme_name


@register.simple_tag()
def get_available_themes(*args, **kwargs):
    """
    Return the available theme choices
    """

    themes = []

    for key, name in ColorTheme.get_color_themes_choices():
        themes.append({
            'key': key,
            'name': name
        })

    return themes


@register.simple_tag()
def primitive_to_javascript(primitive):
    """
    Convert a python primitive to a javascript primitive.

    e.g. True -> true
         'hello' -> '"hello"'
    """

    if type(primitive) is bool:
        return str(primitive).lower()

    elif type(primitive) in [int, float]:
        return primitive

    else:
        # Wrap with quotes
        return format_html("'{}'", primitive)


@register.filter
def keyvalue(dict, key):
    """
    access to key of supplied dict

    usage:
    {% mydict|keyvalue:mykey %}
    """
    return dict.get(key)


@register.simple_tag()
def call_method(obj, method_name, *args):
    """
    enables calling model methods / functions from templates with arguments

    usage:
    {% call_method model_object 'fnc_name' argument1 %}
    """
    method = getattr(obj, method_name)
    return method(*args)


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


@register.simple_tag()
def mail_configured():
    """ Return if mail is configured """
    return bool(settings.EMAIL_HOST)


class I18nStaticNode(StaticNode):
    """
    custom StaticNode
    replaces a variable named *lng* in the path with the current language
    """
    def render(self, context):
        self.path.var = self.path.var.format(lng=context.request.LANGUAGE_CODE)
        ret = super().render(context)
        return ret


# use the dynamic url - tag if in Debugging-Mode
if settings.DEBUG:

    @register.simple_tag()
    def i18n_static(url_name):
        """ simple tag to enable {% url %} functionality instead of {% static %} """
        return reverse(url_name)

else:

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
