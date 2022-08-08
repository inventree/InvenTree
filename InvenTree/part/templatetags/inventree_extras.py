"""This module provides template tags for extra functionality, over and above the built-in Django tags."""

import logging
import os
import sys
from datetime import date, datetime

from django import template
from django.conf import settings as djangosettings
from django.templatetags.static import StaticNode
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

import InvenTree.helpers
from common.models import ColorTheme, InvenTreeSetting, InvenTreeUserSetting
from common.settings import currency_code_default
from InvenTree import settings, version
from plugin import registry
from plugin.models import NotificationUserSetting, PluginSetting

register = template.Library()


logger = logging.getLogger('inventree')


@register.simple_tag()
def define(value, *args, **kwargs):
    """Shortcut function to overcome the shortcomings of the django templating language.

    Use as follows: {% define "hello_world" as hello %}

    Ref: https://stackoverflow.com/questions/1070398/how-to-set-a-value-of-a-variable-inside-a-template-code
    """
    return value


@register.simple_tag(takes_context=True)
def render_date(context, date_object):
    """Renders a date according to the preference of the provided user.

    Note that the user preference is stored using the formatting adopted by moment.js,
    which differs from the python formatting!
    """
    if date_object is None:
        return None

    if type(date_object) == str:

        date_object = date_object.strip()

        # Check for empty string
        if len(date_object) == 0:
            return None

        # If a string is passed, first convert it to a datetime
        try:
            date_object = date.fromisoformat(date_object)
        except ValueError:
            logger.warning(f"Tried to convert invalid date string: {date_object}")
            return None

    # We may have already pre-cached the date format by calling this already!
    user_date_format = context.get('user_date_format', None)

    if user_date_format is None:

        user = context.get('user', None)

        if user and user.is_authenticated:
            # User is specified - look for their date display preference
            user_date_format = InvenTreeUserSetting.get_setting('DATE_DISPLAY_FORMAT', user=user)
        else:
            user_date_format = 'YYYY-MM-DD'

        # Convert the format string to Pythonic equivalent
        replacements = [
            ('YYYY', '%Y'),
            ('MMM', '%b'),
            ('MM', '%m'),
            ('DD', '%d'),
        ]

        for o, n in replacements:
            user_date_format = user_date_format.replace(o, n)

        # Update the context cache
        context['user_date_format'] = user_date_format

    if isinstance(date_object, (datetime, date)):
        return date_object.strftime(user_date_format)
    return date_object


@register.simple_tag()
def decimal(x, *args, **kwargs):
    """Simplified rendering of a decimal number."""
    return InvenTree.helpers.decimal2string(x)


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
def part_allocation_count(build, part, *args, **kwargs):
    """Return the total number of <part> allocated to <build>"""
    return InvenTree.helpers.decimal2string(build.getAllocatedQuantity(part))


@register.simple_tag()
def inventree_in_debug_mode(*args, **kwargs):
    """Return True if the server is running in DEBUG mode."""
    return djangosettings.DEBUG


@register.simple_tag()
def inventree_show_about(user, *args, **kwargs):
    """Return True if the about modal should be shown."""
    if InvenTreeSetting.get_setting('INVENTREE_RESTRICT_ABOUT') and not user.is_superuser:
        return False
    return True


@register.simple_tag()
def inventree_docker_mode(*args, **kwargs):
    """Return True if the server is running as a Docker image."""
    return djangosettings.DOCKER


@register.simple_tag()
def plugins_enabled(*args, **kwargs):
    """Return True if plugins are enabled for the server instance."""
    return djangosettings.PLUGINS_ENABLED


@register.simple_tag()
def plugins_info(*args, **kwargs):
    """Return information about activated plugins."""
    # Check if plugins are even enabled
    if not djangosettings.PLUGINS_ENABLED:
        return False

    # Fetch plugins
    plug_list = [plg for plg in registry.plugins.values() if plg.plugin_config().active]
    # Format list
    return [
        {
            'name': plg.name,
            'slug': plg.slug,
            'version': plg.version
        } for plg in plug_list
    ]


@register.simple_tag()
def inventree_db_engine(*args, **kwargs):
    """Return the InvenTree database backend e.g. 'postgresql'."""
    db = djangosettings.DATABASES['default']

    engine = db.get('ENGINE', _('Unknown database'))

    engine = engine.replace('django.db.backends.', '')

    return engine


@register.simple_tag()
def inventree_instance_name(*args, **kwargs):
    """Return the InstanceName associated with the current database."""
    return version.inventreeInstanceName()


@register.simple_tag()
def inventree_title(*args, **kwargs):
    """Return the title for the current instance - respecting the settings"""
    return version.inventreeInstanceTitle()


@register.simple_tag()
def inventree_logo(**kwargs):
    """Return the InvenTree logo, *or* a custom logo if the user has provided one.

    Returns a path to an image file, which can be rendered in the web interface
    """

    return InvenTree.helpers.getLogoImage(**kwargs)


@register.simple_tag()
def inventree_splash(**kwargs):
    """Return the URL for the InvenTree splash screen, *or* a custom screen if the user has provided one."""

    return InvenTree.helpers.getSplashScren(**kwargs)


@register.simple_tag()
def inventree_base_url(*args, **kwargs):
    """Return the INVENTREE_BASE_URL setting."""
    return InvenTreeSetting.get_setting('INVENTREE_BASE_URL')


@register.simple_tag()
def python_version(*args, **kwargs):
    """Return the current python version."""
    return sys.version.split(' ')[0]


@register.simple_tag()
def inventree_version(shortstring=False, *args, **kwargs):
    """Return InvenTree version string."""
    if shortstring:
        return _("{title} v{version}".format(
            title=version.inventreeInstanceTitle(),
            version=version.inventreeVersion()
        ))
    return version.inventreeVersion()


@register.simple_tag()
def inventree_is_development(*args, **kwargs):
    """Returns True if this is a development version of InvenTree"""
    return version.isInvenTreeDevelopmentVersion()


@register.simple_tag()
def inventree_is_release(*args, **kwargs):
    """Returns True if this is a release version of InvenTree"""
    return not version.isInvenTreeDevelopmentVersion()


@register.simple_tag()
def inventree_docs_version(*args, **kwargs):
    """Returns the InvenTree documentation version"""
    return version.inventreeDocsVersion()


@register.simple_tag()
def inventree_api_version(*args, **kwargs):
    """Return InvenTree API version."""
    return version.inventreeApiVersion()


@register.simple_tag()
def django_version(*args, **kwargs):
    """Return Django version string."""
    return version.inventreeDjangoVersion()


@register.simple_tag()
def inventree_commit_hash(*args, **kwargs):
    """Return InvenTree git commit hash string."""
    return version.inventreeCommitHash()


@register.simple_tag()
def inventree_commit_date(*args, **kwargs):
    """Return InvenTree git commit date string."""
    return version.inventreeCommitDate()


@register.simple_tag()
def inventree_github_url(*args, **kwargs):
    """Return URL for InvenTree github site."""
    return "https://github.com/InvenTree/InvenTree/"


@register.simple_tag()
def inventree_docs_url(*args, **kwargs):
    """Return URL for InvenTree documenation site."""
    tag = version.inventreeDocsVersion()

    return f"https://inventree.readthedocs.io/en/{tag}"


@register.simple_tag()
def inventree_credits_url(*args, **kwargs):
    """Return URL for InvenTree credits site."""
    return "https://inventree.readthedocs.io/en/latest/credits/"


@register.simple_tag()
def default_currency(*args, **kwargs):
    """Returns the default currency code."""
    return currency_code_default()


@register.simple_tag()
def setting_object(key, *args, **kwargs):
    """Return a setting object speciifed by the given key.

    (Or return None if the setting does not exist)
    if a user-setting was requested return that
    """
    if 'plugin' in kwargs:
        # Note, 'plugin' is an instance of an InvenTreePlugin class

        plugin = kwargs['plugin']

        return PluginSetting.get_setting_object(key, plugin=plugin)

    if 'method' in kwargs:
        return NotificationUserSetting.get_setting_object(key, user=kwargs['user'], method=kwargs['method'])

    if 'user' in kwargs:
        return InvenTreeUserSetting.get_setting_object(key, user=kwargs['user'])

    return InvenTreeSetting.get_setting_object(key)


@register.simple_tag()
def settings_value(key, *args, **kwargs):
    """Return a settings value specified by the given key."""
    if 'user' in kwargs:
        if not kwargs['user'] or (kwargs['user'] and kwargs['user'].is_authenticated is False):
            return InvenTreeUserSetting.get_setting(key)
        return InvenTreeUserSetting.get_setting(key, user=kwargs['user'])

    return InvenTreeSetting.get_setting(key)


@register.simple_tag()
def user_settings(user, *args, **kwargs):
    """Return all USER settings as a key:value dict."""
    return InvenTreeUserSetting.allValues(user=user)


@register.simple_tag()
def global_settings(*args, **kwargs):
    """Return all GLOBAL InvenTree settings as a key:value dict."""
    return InvenTreeSetting.allValues()


@register.simple_tag()
def visible_global_settings(*args, **kwargs):
    """Return any global settings which are not marked as 'hidden'."""
    return InvenTreeSetting.allValues(exclude_hidden=True)


@register.simple_tag()
def progress_bar(val, max_val, *args, **kwargs):
    """Render a progress bar element."""
    item_id = kwargs.get('id', 'progress-bar')

    val = InvenTree.helpers.normalize(val)
    max_val = InvenTree.helpers.normalize(max_val)

    if val > max_val:
        style = 'progress-bar-over'
    elif val < max_val:
        style = 'progress-bar-under'
    else:
        style = ''

    percent = float(val / max_val) * 100

    if percent > 100:
        percent = 100
    elif percent < 0:
        percent = 0

    style_tags = []

    max_width = kwargs.get('max_width', None)

    if max_width:
        style_tags.append(f'max-width: {max_width};')

    html = f"""
    <div id='{item_id}' class='progress' style='{" ".join(style_tags)}'>
        <div class='progress-bar {style}' role='progressbar' aria-valuemin='0' aria-valuemax='100' style='width:{percent}%'></div>
        <div class='progress-value'>{val} / {max_val}</div>
    </div>
    """

    return mark_safe(html)


@register.simple_tag()
def get_color_theme_css(username):
    """Return the cutsom theme .css file for the selected user"""
    user_theme_name = get_user_color_theme(username)
    # Build path to CSS sheet
    inventree_css_sheet = os.path.join('css', 'color-themes', user_theme_name + '.css')

    # Build static URL
    inventree_css_static_url = os.path.join(settings.STATIC_URL, inventree_css_sheet)

    return inventree_css_static_url


@register.simple_tag()
def get_user_color_theme(username):
    """Get current user color theme."""
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
    """Return the available theme choices."""
    themes = []

    for key, name in ColorTheme.get_color_themes_choices():
        themes.append({
            'key': key,
            'name': name
        })

    return themes


@register.simple_tag()
def primitive_to_javascript(primitive):
    """Convert a python primitive to a javascript primitive.

    e.g. True -> true
         'hello' -> '"hello"'
    """
    if type(primitive) is bool:
        return str(primitive).lower()

    elif type(primitive) in [int, float]:
        return primitive

    else:
        # Wrap with quotes
        return format_html("'{}'", primitive)  # noqa: P103


@register.filter
def keyvalue(dict, key):
    """Access to key of supplied dict.

    Usage:
    {% mydict|keyvalue:mykey %}
    """
    return dict.get(key)


@register.simple_tag()
def call_method(obj, method_name, *args):
    """Enables calling model methods / functions from templates with arguments.

    Usage:
    {% call_method model_object 'fnc_name' argument1 %}
    """
    method = getattr(obj, method_name)
    return method(*args)


@register.simple_tag()
def authorized_owners(group):
    """Return authorized owners."""
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
    """Return highlighted link to object."""
    ref_url = reverse(url_name, kwargs={'pk': pk})
    return mark_safe(f'<b><a href="{ref_url}">{ref}</a></b>')


@register.simple_tag()
def mail_configured():
    """Return if mail is configured."""
    return bool(settings.EMAIL_HOST)


@register.simple_tag()
def inventree_customize(reference, *args, **kwargs):
    """Return customization values for the user interface."""
    return djangosettings.CUSTOMIZE.get(reference, '')


class I18nStaticNode(StaticNode):
    """Custom StaticNode.

    Replaces a variable named *lng* in the path with the current language
    """

    def render(self, context):  # pragma: no cover
        """Render this node with the determined locale context."""
        self.original = getattr(self, 'original', None)

        if not self.original:
            # Store the original (un-rendered) path template, as it gets overwritten below
            self.original = self.path.var

        if hasattr(context, 'request'):
            self.path.var = self.original.format(lng=context.request.LANGUAGE_CODE)

        ret = super().render(context)

        return ret


# use the dynamic url - tag if in Debugging-Mode
if settings.DEBUG:

    @register.simple_tag()
    def i18n_static(url_name):
        """Simple tag to enable {% url %} functionality instead of {% static %}"""
        return reverse(url_name)

else:  # pragma: no cover

    @register.tag('i18n_static')
    def do_i18n_static(parser, token):
        """Overrides normal static, adds language - lookup for prerenderd files #1485

        Usage (like static):
        {% i18n_static path [as varname] %}
        """
        bits = token.split_contents()
        loc_name = settings.STATICFILES_I18_PREFIX

        # change path to called ressource
        bits[1] = f"'{loc_name}/{{lng}}.{bits[1][1:-1]}'"
        token.contents = ' '.join(bits)

        return I18nStaticNode.handle_token(parser, token)
