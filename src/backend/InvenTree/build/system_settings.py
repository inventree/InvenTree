"""System settings for build app."""

from django.utils.translation import gettext_lazy as _

import build.validators
from common.setting.type import InvenTreeSettingsKeyType, SettingFlag

SYSTEM_SETTINGS: dict[str, InvenTreeSettingsKeyType] = {
    'BUILDORDER_REFERENCE_PATTERN': {
        'name': _('Build Order Reference Pattern'),
        'description': _('Required pattern for generating Build Order reference field'),
        'default': 'BO-{ref:04d}',
        'validator': build.validators.validate_build_order_reference_pattern,
    },
    'BUILDORDER_REQUIRE_RESPONSIBLE': {
        'name': _('Require Responsible Owner'),
        'description': _('A responsible owner must be assigned to each order'),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_REQUIRE_ACTIVE_PART': {
        'name': _('Require Active Part'),
        'description': _('Prevent build order creation for inactive parts'),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_REQUIRE_LOCKED_PART': {
        'name': _('Require Locked Part'),
        'description': _('Prevent build order creation for unlocked parts'),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_REQUIRE_VALID_BOM': {
        'name': _('Require Valid BOM'),
        'description': _('Prevent build order creation unless BOM has been validated'),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_REQUIRE_CLOSED_CHILDS': {
        'name': _('Require Closed Child Orders'),
        'description': _(
            'Prevent build order completion until all child orders are closed'
        ),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_EXTERNAL_BUILDS': {
        'name': _('External Build Orders'),
        'description': _('Enable external build order functionality'),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_EXTERNAL_REQUIRED': {
        'name': _('Require External Build Orders'),
        'description': _(
            'Require an external build order when ordering assembled parts from an external supplier'
        ),
        'default': False,
        'validator': bool,
    },
    'PREVENT_BUILD_COMPLETION_HAVING_INCOMPLETED_TESTS': {
        'name': _('Block Until Tests Pass'),
        'description': _(
            'Prevent build outputs from being completed until all required tests pass'
        ),
        'default': False,
        'validator': bool,
    },
    'BUILDORDER_ENABLED': {
        'name': _('Enable Build Orders'),
        'description': _('Enable build order functionality in the user interface'),
        'validator': bool,
        'default': True,
        'flags': [SettingFlag.TOGGLE],
    },
}
