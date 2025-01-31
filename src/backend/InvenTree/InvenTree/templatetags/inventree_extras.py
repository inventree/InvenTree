"""This module provides template tags for extra functionality, over and above the built-in Django tags."""

from datetime import date, datetime

from django import template
from django.conf import settings as djangosettings
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

import common.models
import InvenTree.helpers
import InvenTree.helpers_model
import plugin.models
from common.currency import currency_code_default
from common.settings import get_global_setting
from InvenTree import settings, version
from plugin import registry
from plugin.plugin import InvenTreePlugin

register = template.Library()


import structlog

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
def render_date(context, date_object):
    """Renders a date according to the preference of the provided user.

    Note that the user preference is stored using the formatting adopted by moment.js,
    which differs from the python formatting!
    """
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

    # We may have already pre-cached the date format by calling this already!
    user_date_format = context.get('user_date_format', None)

    if user_date_format is None:
        user = context.get('user', None)

        if user and user.is_authenticated:
            # User is specified - look for their date display preference
            user_date_format = common.models.InvenTreeUserSetting.get_setting(
                'DATE_DISPLAY_FORMAT', user=user
            )
        else:
            user_date_format = 'YYYY-MM-DD'

        # Convert the format string to Pythonic equivalent
        replacements = [('YYYY', '%Y'), ('MMM', '%b'), ('MM', '%m'), ('DD', '%d')]

        for o, n in replacements:
            user_date_format = user_date_format.replace(o, n)

        # Update the context cache
        context['user_date_format'] = user_date_format

    if isinstance(date_object, (datetime, date)):
        return date_object.strftime(user_date_format)
    return date_object


@register.simple_tag
def render_currency(money, **kwargs):
    """Render a currency / Money object."""
    return InvenTree.helpers_model.render_currency(money, **kwargs)


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
def plugins_enabled(*args, **kwargs):
    """Return True if plugins are enabled for the server instance."""
    return djangosettings.PLUGINS_ENABLED


@register.simple_tag()
def plugins_install_disabled(*args, **kwargs):
    """Return True if plugin install is disabled for the server instance."""
    return djangosettings.PLUGINS_INSTALL_DISABLED


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
        {'name': plg.name, 'slug': plg.slug, 'version': plg.version}
        for plg in plug_list
    ]


@register.simple_tag()
def inventree_db_engine(*args, **kwargs):
    """Return the InvenTree database backend e.g. 'postgresql'."""
    return version.inventreeDatabase() or _('Unknown database')


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

    Returns a path to an image file, which can be rendered in the web interface
    """
    return InvenTree.helpers.getLogoImage(**kwargs)


@register.simple_tag()
def inventree_splash(**kwargs):
    """Return the URL for the InvenTree splash screen, *or* a custom screen if the user has provided one."""
    return InvenTree.helpers.getSplashScreen(**kwargs)


@register.simple_tag()
def inventree_base_url(*args, **kwargs):
    """Return the base URL of the InvenTree server."""
    return InvenTree.helpers_model.get_base_url()


@register.simple_tag()
def python_version(*args, **kwargs):
    """Return the current python version."""
    return version.inventreePythonVersion()


@register.simple_tag()
def inventree_version(shortstring=False, *args, **kwargs):
    """Return InvenTree version string."""
    if shortstring:
        return f'{version.inventreeInstanceTitle()} v{version.inventreeVersion()}'
    return version.inventreeVersion()


@register.simple_tag()
def inventree_is_development(*args, **kwargs):
    """Returns True if this is a development version of InvenTree."""
    return version.isInvenTreeDevelopmentVersion()


@register.simple_tag()
def inventree_is_release(*args, **kwargs):
    """Returns True if this is a release version of InvenTree."""
    return not version.isInvenTreeDevelopmentVersion()


@register.simple_tag()
def inventree_docs_version(*args, **kwargs):
    """Returns the InvenTree documentation version."""
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
def inventree_installer(*args, **kwargs):
    """Return InvenTree package installer string."""
    return version.inventreeInstaller()


@register.simple_tag()
def inventree_branch(*args, **kwargs):
    """Return InvenTree git branch string."""
    return version.inventreeBranch()


@register.simple_tag()
def inventree_target(*args, **kwargs):
    """Return InvenTree target string."""
    return version.inventreeTarget()


@register.simple_tag()
def inventree_platform(*args, **kwargs):
    """Return InvenTree platform string."""
    return version.inventreePlatform()


@register.simple_tag()
def inventree_github_url(*args, **kwargs):
    """Return URL for InvenTree github site."""
    return version.inventreeGithubUrl()


@register.simple_tag()
def inventree_docs_url(*args, **kwargs):
    """Return URL for InvenTree documentation site."""
    return version.inventreeDocUrl()


@register.simple_tag()
def inventree_app_url(*args, **kwargs):
    """Return URL for InvenTree app site."""
    return version.inventreeAppUrl()


@register.simple_tag()
def inventree_credits_url(*args, **kwargs):
    """Return URL for InvenTree credits site."""
    return version.inventreeCreditsUrl()


@register.simple_tag()
def default_currency(*args, **kwargs):
    """Returns the default currency code."""
    return currency_code_default()


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


@register.simple_tag()
def user_settings(user, *args, **kwargs):
    """Return all USER settings as a key:value dict."""
    return common.models.InvenTreeUserSetting.allValues(user=user)


@register.simple_tag()
def global_settings(*args, **kwargs):
    """Return all GLOBAL InvenTree settings as a key:value dict."""
    return common.models.InvenTreeSetting.allValues()


@register.simple_tag()
def visible_global_settings(*args, **kwargs):
    """Return any global settings which are not marked as 'hidden'."""
    return common.models.InvenTreeSetting.allValues(exclude_hidden=True)


@register.filter
def keyvalue(dict, key):
    """Access to key of supplied dict.

    Usage:
    {% mydict|keyvalue:mykey %}
    """
    return dict.get(key)


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
    try:
        ref_url = reverse(url_name, kwargs={'pk': pk})
        return mark_safe(f'<b><a href="{ref_url}">{ref}</a></b>')
    except NoReverseMatch:
        return None


@register.simple_tag()
def mail_configured():
    """Return if mail is configured."""
    return bool(settings.EMAIL_HOST)


@register.simple_tag()
def inventree_customize(reference, *args, **kwargs):
    """Return customization values for the user interface."""
    return djangosettings.CUSTOMIZE.get(reference, '')


@register.simple_tag()
def admin_index(user):
    """Return a URL for the admin interface."""
    if not djangosettings.INVENTREE_ADMIN_ENABLED:
        return ''

    if not user.is_staff:
        return ''

    return reverse('admin:index')


@register.simple_tag()
def admin_url(user, table, pk):
    """Generate a link to the admin site for the given model instance.

    - If the admin site is disabled, an empty URL is returned
    - If the user is not a staff user, an empty URL is returned
    - If the user does not have the correct permission, an empty URL is returned
    """
    app, model = table.strip().split('.')

    from django.urls import reverse

    if not djangosettings.INVENTREE_ADMIN_ENABLED:
        return ''

    if not user.is_staff:
        return ''

    # Check the user has the correct permission
    perm_string = f'{app}.change_{model}'
    if not user.has_perm(perm_string):
        return ''

    # Fallback URL
    url = reverse(f'admin:{app}_{model}_changelist')

    if pk:
        try:
            url = reverse(f'admin:{app}_{model}_change', args=(pk,))
        except NoReverseMatch:
            pass

    return url
