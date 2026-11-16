"""System settings definition."""

import json
import os
import uuid
from importlib import import_module
from importlib.util import find_spec

from django.apps import apps
from django.conf import settings as django_settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, URLValidator
from django.utils.translation import gettext_lazy as _

import common.currency
import common.validators
from common.setting.type import InvenTreeSettingsKeyType, SettingFlag


def validate_internal_company(value):
    """Validate that the provided value is empty, or references an internal company."""
    from company.models import Company

    if value in [None, '']:
        return

    try:
        pk = int(value)
    except (TypeError, ValueError):
        raise ValidationError({'value': _('Invalid company')})

    if not Company.objects.filter(pk=pk, is_internal=True).exists():
        raise ValidationError({
            'value': _('Selected company must be marked as an internal company')
        })


def _get_site_object():
    """Return the first site object, or None if it doesn't exist."""
    if not django_settings.SITE_MULTI:
        return  # pragma: no cover

    try:
        from django.contrib.sites.models import Site
    except (ImportError, RuntimeError):
        # Multi-site support not enabled
        return  # pragma: no cover

    site_obj = Site.objects.all().order_by('id').first()
    if site_obj is None:
        return  # pragma: no cover
    return site_obj


def update_instance_name(setting):
    """Update the first site objects name to instance name."""
    if site_obj := _get_site_object():
        site_obj.name = setting.value
        site_obj.save()


def update_instance_url(setting):
    """Update the first site objects domain to url."""
    if site_obj := _get_site_object():
        site_obj.domain = setting.value
        site_obj.save()


def settings_group_options():
    """Build up group tuple for settings based on your choices."""
    from django.contrib.auth.models import Group

    return [('', _('No group')), *[(str(a.pk), str(a)) for a in Group.objects.all()]]


def reload_plugin_registry(setting):
    """When a core plugin setting is changed, reload the plugin registry."""
    from common.models import logger
    from plugin import registry

    logger.info("Reloading plugin registry due to change in setting '%s'", setting.key)

    registry.reload_plugins(full_reload=True, force_reload=True, collect=True)


def enforce_mfa(setting):
    """Enforce multifactor authentication for all users."""
    from allauth.usersessions.models import UserSession

    from common.models import logger

    logger.info(
        'Enforcing multifactor authentication for all users by signing out all sessions.'
    )
    for session in UserSession.objects.all():
        session.end()
    logger.info('All user sessions have been ended.')


def barcode_plugins() -> list:
    """Return a list of plugin choices which can be used for barcode generation."""
    try:
        from plugin import PluginMixinEnum, registry

        plugins = registry.with_mixin(PluginMixinEnum.BARCODE, active=True)
    except Exception:  # pragma: no cover
        plugins = []

    return [
        (plug.slug, plug.human_name) for plug in plugins if plug.has_barcode_generation
    ]


def default_uuid4() -> str:
    """Return a default UUID4 value."""
    return str(uuid.uuid4())


class BaseURLValidator(URLValidator):
    """Validator for the InvenTree base URL.

    Rules:
    - Allow empty value
    - Allow value without specified TLD (top level domain)
    """

    def __init__(self, schemes=None, **kwargs):
        """Custom init routine."""
        super().__init__(schemes, **kwargs)

        # Override default host_re value - allow optional tld regex
        self.host_re = (
            '('
            + self.hostname_re
            + self.domain_re
            + f'({self.tld_re})?'
            + '|localhost)'
        )

    def __call__(self, value):
        """Make sure empty values pass."""
        value = str(value).strip()

        # If a configuration level value has been specified, prevent change
        if django_settings.SITE_URL and value != django_settings.SITE_URL:
            raise ValidationError(_('Site URL is locked by configuration'))

        if len(value) == 0:
            pass

        else:
            super().__call__(value)


class SystemSetId:
    """Shared system settings identifiers."""

    GLOBAL_WARNING = '_GLOBAL_WARNING'


SYSTEM_SETTINGS: dict[str, InvenTreeSettingsKeyType] = {
    'SERVER_RESTART_REQUIRED': {
        'name': _('Restart required'),
        'description': _('A setting has been changed which requires a server restart'),
        'default': False,
        'validator': bool,
        'hidden': True,
        'flags': [SettingFlag.INTERNAL],
    },
    '_PENDING_MIGRATIONS': {
        'name': _('Pending migrations'),
        'description': _('Number of pending database migrations'),
        'default': 0,
        'validator': int,
        'flags': [SettingFlag.INTERNAL],
    },
    SystemSetId.GLOBAL_WARNING: {
        'name': _('Active warning codes'),
        'description': _('A dict of active warning codes'),
        'validator': json.loads,
        'default': '{}',
        'hidden': True,
        'flags': [SettingFlag.INTERNAL],
    },
    'INVENTREE_INSTANCE_ID': {
        'name': _('Instance ID'),
        'description': _('Unique identifier for this InvenTree instance'),
        'default': default_uuid4,
        'hidden': True,
    },
    'INVENTREE_ANNOUNCE_ID': {
        'name': _('Announce ID'),
        'description': _(
            'Announce the instance ID of the server in the server status info (unauthenticated)'
        ),
        'default': False,
        'validator': bool,
    },
    'INVENTREE_LINK_PROOF': {
        'name': _('Allow Link Proof'),
        'description': _(
            'Allow other instances to verify the server identity without revealing the instance ID'
        ),
        'default': True,
        'validator': bool,
    },
    'INVENTREE_INSTANCE': {
        'name': _('Server Instance Name'),
        'default': 'InvenTree',
        'description': _('String descriptor for the server instance'),
        'after_save': update_instance_name,
    },
    'INVENTREE_INSTANCE_TITLE': {
        'name': _('Use instance name'),
        'description': _('Use the instance name in the title-bar'),
        'validator': bool,
        'default': False,
    },
    'INVENTREE_RESTRICT_ABOUT': {
        'name': _('Restrict showing `about`'),
        'description': _('Show the `about` modal only to superusers'),
        'validator': bool,
        'default': False,
    },
    'INVENTREE_SHOW_SUPERUSER_BANNER': {
        'name': _('Show superuser banner'),
        'description': _('Show a warning banner in the UI when logged in as superuser'),
        'validator': bool,
        'default': True,
        'flags': [SettingFlag.SECURITY],
    },
    'INVENTREE_SHOW_ADMIN_BANNER': {
        'name': _('Show admin banner'),
        'description': _('Show a warning banner in the UI when logged in as admin'),
        'validator': bool,
        'default': False,
    },
    'INVENTREE_COMPANY_NAME': {
        'name': _('Company name'),
        'description': _('Internal company name'),
        'default': 'My company name',
    },
    'INVENTREE_DEFAULT_INTERNAL_COMPANY': {
        'name': _('Default internal company'),
        'description': _('Internal company which represents this organization'),
        'default': '',
        'model': 'company.company',
        'model_filters': {'is_internal': True},
        'validator': validate_internal_company,
    },
    'INVENTREE_BASE_URL': {
        'name': _('Base URL'),
        'description': _('Base URL for server instance'),
        'validator': BaseURLValidator(),
        'default': '',
        'after_save': update_instance_url,
    },
    'INVENTREE_DEFAULT_CURRENCY': {
        'name': _('Default Currency'),
        'description': _('Select base currency for pricing calculations'),
        'default': 'USD',
        'choices': common.currency.currency_code_mappings,
        'after_save': common.currency.after_change_currency,
    },
    'CURRENCY_CODES': {
        'name': _('Supported Currencies'),
        'description': _('List of supported currency codes'),
        'default': common.currency.currency_codes_default_list(),
        'validator': common.currency.validate_currency_codes,
        'after_save': common.currency.after_change_currency,
    },
    'CURRENCY_UPDATE_INTERVAL': {
        'name': _('Currency Update Interval'),
        'description': _('How often to update exchange rates (set to zero to disable)'),
        'default': 1,
        'units': _('days'),
        'validator': [int, MinValueValidator(0)],
    },
    'CURRENCY_UPDATE_PLUGIN': {
        'name': _('Currency Update Plugin'),
        'description': _('Currency update plugin to use'),
        'choices': common.currency.currency_exchange_plugins,
        'default': 'inventreecurrencyexchange',
    },
    'INVENTREE_UPLOAD_MAX_SIZE': {
        'name': _('Upload Size Limit'),
        'description': _('Maximum allowable upload size for images and files'),
        'units': 'MB',
        'default': 10,
        'validator': [int, MinValueValidator(1)],
        'flags': [SettingFlag.SECURITY],
    },
    'INVENTREE_STRICT_URLS': {
        'name': _('Strict URL Validation'),
        'description': _('Require schema specification when validating URLs'),
        'validator': bool,
        'default': True,
        'flags': [SettingFlag.SECURITY],
    },
    'INVENTREE_UPDATE_CHECK_INTERVAL': {
        'name': _('Update Check Interval'),
        'description': _('How often to check for updates (set to zero to disable)'),
        'validator': [int, MinValueValidator(0)],
        'default': 7,
        'units': _('days'),
    },
    'INVENTREE_BACKUP_ENABLE': {
        'name': _('Automatic Backup'),
        'description': _('Enable automatic backup of database and media files'),
        'validator': bool,
        'default': False,
    },
    'INVENTREE_BACKUP_DAYS': {
        'name': _('Auto Backup Interval'),
        'description': _('Specify number of days between automated backup events'),
        'validator': [int, MinValueValidator(1)],
        'default': 1,
        'units': _('days'),
    },
    'INVENTREE_DELETE_TASKS_DAYS': {
        'name': _('Task Deletion Interval'),
        'description': _(
            'Background task results will be deleted after specified number of days'
        ),
        'default': 30,
        'units': _('days'),
        'validator': [int, MinValueValidator(7)],
    },
    'INVENTREE_DELETE_ERRORS_DAYS': {
        'name': _('Error Log Deletion Interval'),
        'description': _('Error logs will be deleted after specified number of days'),
        'default': 30,
        'units': _('days'),
        'validator': [int, MinValueValidator(7)],
    },
    'INVENTREE_DELETE_NOTIFICATIONS_DAYS': {
        'name': _('Notification Deletion Interval'),
        'description': _(
            'User notifications will be deleted after specified number of days'
        ),
        'default': 30,
        'units': _('days'),
        'validator': [int, MinValueValidator(7)],
    },
    'INVENTREE_DELETE_EMAIL_DAYS': {
        'name': _('Email Deletion Interval'),
        'description': _(
            'Email messages will be deleted after specified number of days'
        ),
        'default': 30,
        'units': _('days'),
        'validator': [int, MinValueValidator(7)],
    },
    'INVENTREE_PROTECT_EMAIL_LOG': {
        'name': _('Protect Email Log'),
        'description': _('Prevent deletion of email log entries'),
        'default': False,
        'validator': bool,
    },
    'BARCODE_ENABLE': {
        'name': _('Barcode Support'),
        'description': _('Enable barcode scanner support in the web interface'),
        'default': True,
        'validator': bool,
        'flags': [SettingFlag.TOGGLE],
    },
    'BARCODE_STORE_RESULTS': {
        'name': _('Store Barcode Results'),
        'description': _('Store barcode scan results in the database'),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.TOGGLE],
    },
    'BARCODE_RESULTS_MAX_NUM': {
        'name': _('Barcode Scans Maximum Count'),
        'description': _('Maximum number of barcode scan results to store'),
        'default': 100,
        'validator': [int, MinValueValidator(1)],
    },
    'BARCODE_INPUT_DELAY': {
        'name': _('Barcode Input Delay'),
        'description': _('Barcode input processing delay time'),
        'default': 50,
        'validator': [int, MinValueValidator(1)],
        'units': 'ms',
    },
    'BARCODE_WEBCAM_SUPPORT': {
        'name': _('Barcode Webcam Support'),
        'description': _('Allow barcode scanning via webcam in browser'),
        'default': True,
        'validator': bool,
        'flags': [SettingFlag.TOGGLE],
    },
    'BARCODE_SHOW_TEXT': {
        'name': _('Barcode Show Data'),
        'description': _('Display barcode data in browser as text'),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.TOGGLE],
    },
    'BARCODE_GENERATION_PLUGIN': {
        'name': _('Barcode Generation Plugin'),
        'description': _('Plugin to use for internal barcode data generation'),
        'choices': barcode_plugins,
        'default': 'inventreebarcode',
    },
    'PARAMETER_ENFORCE_UNITS': {
        'name': _('Enforce Parameter Units'),
        'description': _(
            'If units are provided, parameter values must match the specified units'
        ),
        'default': True,
        'validator': bool,
    },
    'SERIAL_NUMBER_GLOBALLY_UNIQUE': {
        'name': _('Globally Unique Serials'),
        'description': _('Serial numbers for stock items must be globally unique'),
        'default': False,
        'validator': bool,
    },
    # login / SSO
    'LOGIN_ENABLE_PWD_FORGOT': {
        'name': _('Enable password forgot'),
        'description': _('Enable password forgot function on the login pages'),
        'default': True,
        'validator': bool,
        'flags': [SettingFlag.SECURITY],
    },
    'LOGIN_ENABLE_REG': {
        'name': _('Enable registration'),
        'description': _('Enable self-registration for users on the login pages'),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.SECURITY],
    },
    'LOGIN_ENABLE_SSO': {
        'name': _('Enable SSO'),
        'description': _('Enable SSO on the login pages'),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.SECURITY],
    },
    'LOGIN_ENABLE_SSO_REG': {
        'name': _('Enable SSO registration'),
        'description': _(
            'Enable self-registration via SSO for users on the login pages'
        ),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.SECURITY],
    },
    'LOGIN_ENABLE_SSO_GROUP_SYNC': {
        'name': _('Enable SSO group sync'),
        'description': _(
            'Enable synchronizing InvenTree groups with groups provided by the IdP'
        ),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.SECURITY],
    },
    'SSO_GROUP_KEY': {
        'name': _('SSO group key'),
        'description': _('The name of the groups claim attribute provided by the IdP'),
        'default': 'groups',
        'validator': str,
        'flags': [SettingFlag.SECURITY],
    },
    'SSO_GROUP_MAP': {
        'name': _('SSO group map'),
        'description': _(
            'A mapping from SSO groups to local InvenTree groups. If the local group does not exist, it will be created.'
        ),
        'validator': json.loads,
        'flags': [SettingFlag.SECURITY],
        'default': '{}',
    },
    'SSO_REMOVE_GROUPS': {
        'name': _('Remove groups outside of SSO'),
        'description': _(
            'Whether groups assigned to the user should be removed if they are not backend by the IdP. Disabling this setting might cause security issues'
        ),
        'default': True,
        'validator': bool,
        'confirm': True,
        'confirm_text': _(
            'Disabling this setting will stop cleaning up groups that external users no longer belong to. This might cause security issues.'
        ),
        'flags': [SettingFlag.SECURITY],
    },
    'LOGIN_MAIL_REQUIRED': {
        'name': _('Email required'),
        'description': _('Require user to supply mail on signup'),
        'default': False,
        'validator': bool,
    },
    'LOGIN_SIGNUP_SSO_AUTO': {
        'name': _('Auto-fill SSO users'),
        'description': _('Automatically fill out user-details from SSO account-data'),
        'default': True,
        'validator': bool,
    },
    'LOGIN_SIGNUP_MAIL_TWICE': {
        'name': _('Mail twice'),
        'description': _('On signup ask users twice for their mail'),
        'default': False,
        'validator': bool,
    },
    'LOGIN_SIGNUP_PWD_TWICE': {
        'name': _('Password twice'),
        'description': _('On signup ask users twice for their password'),
        'default': True,
        'validator': bool,
    },
    'LOGIN_SIGNUP_MAIL_RESTRICTION': {
        'name': _('Allowed domains'),
        'description': _(
            'Restrict signup to certain domains (comma-separated, starting with @)'
        ),
        'default': '',
        'before_save': common.validators.validate_email_domains,
        'flags': [SettingFlag.SECURITY],
    },
    'SIGNUP_GROUP': {
        'name': _('Group on signup'),
        'description': _(
            'Group to which new users are assigned on registration. If SSO group sync is enabled, this group is only set if no group can be assigned from the IdP.'
        ),
        'default': '',
        'choices': settings_group_options,
        'flags': [SettingFlag.SECURITY],
    },
    'LOGIN_ENFORCE_MFA': {
        'name': _('Enforce MFA'),
        'description': _('Users must use multifactor security.'),
        'default': False,
        'validator': bool,
        'confirm': True,
        'confirm_text': _(
            'Enabling this setting will require all users to set up multifactor authentication. All sessions will be disconnected immediately, and API tokens of users without multifactor authentication will stop working.'
        ),
        'flags': [SettingFlag.SECURITY],
        'after_save': enforce_mfa,
    },
    'PLUGIN_ON_STARTUP': {
        'name': _('Check plugins on startup'),
        'description': _(
            'Check that all plugins are installed on startup - enable in container environments'
        ),
        'default': str(os.getenv('INVENTREE_DOCKER', 'False')).lower() in ['1', 'true'],
        'validator': bool,
        'requires_restart': True,
    },
    'PLUGIN_UPDATE_CHECK': {
        'name': _('Check for plugin updates'),
        'description': _('Enable periodic checks for updates to installed plugins'),
        'default': True,
        'validator': bool,
    },
    # Settings for plugin mixin features
    'ENABLE_PLUGINS_URL': {
        'name': _('Enable URL integration'),
        'description': _('Enable plugins to add URL routes'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
        'flags': [SettingFlag.TOGGLE],
    },
    'ENABLE_PLUGINS_NAVIGATION': {
        'name': _('Enable navigation integration'),
        'description': _('Enable plugins to integrate into navigation'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
        'flags': [SettingFlag.TOGGLE],
    },
    'ENABLE_PLUGINS_APP': {
        'name': _('Enable app integration'),
        'description': _('Enable plugins to add apps'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
        'flags': [SettingFlag.TOGGLE],
    },
    'ENABLE_PLUGINS_SCHEDULE': {
        'name': _('Enable schedule integration'),
        'description': _('Enable plugins to run scheduled tasks'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
        'flags': [SettingFlag.TOGGLE],
    },
    'ENABLE_PLUGINS_EVENTS': {
        'name': _('Enable event integration'),
        'description': _('Enable plugins to respond to internal events'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
        'flags': [SettingFlag.TOGGLE],
    },
    'ENABLE_PLUGINS_INTERFACE': {
        'name': _('Enable interface integration'),
        'description': _('Enable plugins to integrate into the user interface'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
        'flags': [SettingFlag.TOGGLE],
    },
    'ENABLE_PLUGINS_MAILS': {
        'name': _('Enable mail integration'),
        'description': _('Enable plugins to process outgoing/incoming mails'),
        'default': False,
        'validator': bool,
        'after_save': reload_plugin_registry,
        'flags': [SettingFlag.TOGGLE],
    },
    'PROJECT_CODES_ENABLED': {
        'name': _('Enable project codes'),
        'description': _('Enable project codes for tracking projects'),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.TOGGLE],
    },
    'AUDIT_LOG_ENABLED': {
        'name': _('Enable Audit Log'),
        'description': _('Record a history of changes made to supported models'),
        'default': True,
        'validator': bool,
    },
    'AUDIT_LOG_DELETE_OLD_ENTRIES': {
        'name': _('Delete Old Audit Log Entries'),
        'description': _(
            'Delete audit log entries older than the specified number of days'
        ),
        'default': False,
        'validator': bool,
    },
    'AUDIT_LOG_DELETE_KEEP_SUMMARY': {
        'name': _('Retain Audit Log Summary'),
        'description': _(
            'When deleting old audit log entries, always keep the creation entry and the most recent entry for each item'
        ),
        'default': True,
        'validator': bool,
    },
    'AUDIT_LOG_DELETE_DAYS': {
        'name': _('Audit Log Deletion Interval'),
        'description': _(
            'Audit log entries will be deleted after specified number of days'
        ),
        'default': 365,
        'units': _('days'),
        'validator': [int, MinValueValidator(7)],
    },
    'DISPLAY_FULL_NAMES': {
        'name': _('Display Users full names'),
        'description': _('Display Users full names instead of usernames'),
        'default': False,
        'validator': bool,
    },
    'DISPLAY_PROFILE_INFO': {
        'name': _('Display User Profiles'),
        'description': _('Display Users Profiles on their profile page'),
        'default': True,
        'validator': bool,
    },
    'WEEK_STARTS_ON': {
        'name': _('Week Starts On'),
        'description': _('Starting day of the week, for display in calendar views'),
        'default': '1',
        'choices': [
            ('0', _('Sunday')),
            ('1', _('Monday')),
            ('2', _('Tuesday')),
            ('3', _('Wednesday')),
            ('4', _('Thursday')),
            ('5', _('Friday')),
            ('6', _('Saturday')),
        ],
    },
    'CALENDAR_HORIZON_MONTHS': {
        'name': _('Calendar Horizon'),
        'description': _(
            'Number of months into the future to display in calendar views'
        ),
        'default': 12,
        'validator': [int, MinValueValidator(1)],
        'units': _('months'),
    },
    'TEST_STATION_DATA': {
        'name': _('Enable Test Station Data'),
        'description': _('Enable test station data collection for test results'),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.TOGGLE],
    },
    'MACHINE_PING_ENABLED': {
        'name': _('Enable Machine Ping'),
        'description': _(
            'Enable periodic ping task of registered machines to check their status'
        ),
        'default': True,
        'validator': bool,
    },
}
_settings_collected = False


def collect_system_settings() -> None:
    """Collect the domain-specific system settings from built-in apps."""
    global _settings_collected

    if _settings_collected:
        return

    _settings_collected = True

    for app in apps.get_app_configs():
        module_name = f'{app.name}.system_settings'

        try:
            if find_spec(module_name) is None:
                continue
        except ModuleNotFoundError:  # pragma: no cover
            continue

        settings = import_module(module_name).SYSTEM_SETTINGS

        duplicates = sorted(SYSTEM_SETTINGS.keys() & settings.keys())
        if duplicates:
            raise ValueError(f'Duplicate system settings in {app.name}: {duplicates}')

        SYSTEM_SETTINGS.update(settings)
