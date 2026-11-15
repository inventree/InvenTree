"""System settings for the report app."""

from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

import report.helpers
from common.setting.type import InvenTreeSettingsKeyType, SettingFlag

SYSTEM_SETTINGS: dict[str, InvenTreeSettingsKeyType] = {
    'LABEL_ENABLE': {
        'name': _('Enable label printing'),
        'description': _('Enable label printing from the web interface'),
        'default': True,
        'validator': bool,
        'flags': [SettingFlag.TOGGLE],
    },
    'LABEL_DPI': {
        'name': _('Label Image DPI'),
        'description': _(
            'DPI resolution when generating image files to supply to label printing plugins'
        ),
        'default': 300,
        'validator': [int, MinValueValidator(100)],
    },
    'REPORT_ENABLE': {
        'name': _('Enable Reports'),
        'description': _('Enable generation of reports'),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.TOGGLE],
    },
    'REPORT_DEBUG_MODE': {
        'name': _('Debug Mode'),
        'description': _('Generate reports in debug mode (HTML output)'),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.SECURITY],
    },
    'REPORT_FETCH_URLS': {
        'name': _('Report URL Fetching'),
        'description': _('Allow fetching of remote URLs when generating reports'),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.SECURITY],
    },
    'REPORT_LOG_ERRORS': {
        'name': _('Log Report Errors'),
        'description': _('Log errors which occur when generating reports'),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.SECURITY],
    },
    'REPORT_DEFAULT_PAGE_SIZE': {
        'name': _('Page Size'),
        'description': _('Default page size for PDF reports'),
        'default': 'A4',
        'choices': report.helpers.report_page_size_options,
    },
}
