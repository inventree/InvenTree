"""System settings for the stock app."""

from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

import common.validators
import stock.validators
from common.setting.type import InvenTreeSettingsKeyType, SettingFlag

SYSTEM_SETTINGS: dict[str, InvenTreeSettingsKeyType] = {
    'STOCK_DELETE_DEPLETED_DEFAULT': {
        'name': _('Delete Depleted Stock'),
        'description': _('Determines default behavior when a stock item is depleted'),
        'default': True,
        'validator': bool,
    },
    'STOCK_ALLOW_EDIT_SERIAL': {
        'name': _('Allow Edit Serial Number'),
        'description': _('Allow editing of serial number for stock items'),
        'default': True,
        'validator': bool,
    },
    'STOCK_ALLOW_DELETE_SERIALIZED': {
        'name': _('Delete Serialized Stock'),
        'description': _('Allow deletion of stock items which have a serial number'),
        'default': True,
        'validator': bool,
    },
    'STOCK_BATCH_CODE_TEMPLATE': {
        'name': _('Batch Code Template'),
        'description': _(
            'Template for generating default batch codes for stock items (leave blank to disable)'
        ),
        'default': '',
        'validator': stock.validators.validate_batch_code_template,
    },
    'STOCK_ENABLE_EXPIRY': {
        'name': _('Stock Expiry'),
        'description': _('Enable stock expiry functionality'),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.TOGGLE],
    },
    'STOCK_ALLOW_EXPIRED_SALE': {
        'name': _('Sell Expired Stock'),
        'description': _('Allow sale of expired stock'),
        'default': False,
        'validator': bool,
    },
    'STOCK_STALE_DAYS': {
        'name': _('Stock Stale Time'),
        'description': _(
            'Number of days stock items are considered stale before expiring (set to zero to disable). Requires stock expiry to be enabled'
        ),
        'default': 0,
        'units': _('days'),
        'validator': [int, MinValueValidator(0)],
    },
    'STOCK_ALLOW_EXPIRED_BUILD': {
        'name': _('Build Expired Stock'),
        'description': _('Allow building with expired stock'),
        'default': False,
        'validator': bool,
    },
    'STOCK_OWNERSHIP_CONTROL': {
        'name': _('Stock Ownership Control'),
        'description': _('Enable ownership control over stock locations and items'),
        'default': False,
        'validator': bool,
        'flags': [SettingFlag.TOGGLE],
    },
    'STOCK_LOCATION_DEFAULT_ICON': {
        'name': _('Stock Location Default Icon'),
        'description': _('Stock location default icon (empty means no icon)'),
        'default': '',
        'validator': common.validators.validate_icon,
    },
    'STOCK_ENFORCE_BOM_INSTALLATION': {
        'name': _('Check BOM when installing items'),
        'description': _(
            'Installed stock items must exist in the BOM for the parent part'
        ),
        'default': True,
        'validator': bool,
    },
    'STOCK_ALLOW_OUT_OF_STOCK_TRANSFER': {
        'name': _('Allow Out of Stock Transfer'),
        'description': _(
            'Allow stock items which are not in stock to be transferred between stock locations'
        ),
        'default': False,
        'validator': bool,
    },
    'STOCK_MERGE_ON_TRANSFER': {
        'name': _('Merge stock with existing stock on transfer by default'),
        'description': _(
            'Default state for merge stock on transfer behaviour. (Can be changed per transfer if desired)'
        ),
        'default': False,
        'validator': bool,
    },
}


def stock_expiry_enabled():
    """Returns True if the stock expiry feature is enabled."""
    from common.models import InvenTreeSetting

    return InvenTreeSetting.get_setting('STOCK_ENABLE_EXPIRY', False, create=False)
