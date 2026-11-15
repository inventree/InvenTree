"""System settings for the pricing app."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

import pricing.validators
from common.setting.type import InvenTreeSettingsKeyType

SYSTEM_SETTINGS: dict[str, InvenTreeSettingsKeyType] = {
    'PRICING_DECIMAL_PLACES_MIN': {
        'name': _('Minimum Pricing Decimal Places'),
        'description': _(
            'Minimum number of decimal places to display when rendering pricing data'
        ),
        'default': 0,
        'validator': [
            int,
            MinValueValidator(0),
            MaxValueValidator(4),
            pricing.validators.validate_decimal_places_min,
        ],
    },
    'PRICING_DECIMAL_PLACES': {
        'name': _('Maximum Pricing Decimal Places'),
        'description': _(
            'Maximum number of decimal places to display when rendering pricing data'
        ),
        'default': 6,
        'validator': [
            int,
            MinValueValidator(2),
            MaxValueValidator(6),
            pricing.validators.validate_decimal_places_max,
        ],
    },
    'PRICING_USE_SUPPLIER_PRICING': {
        'name': _('Use Supplier Pricing'),
        'description': _(
            'Include supplier price breaks in overall pricing calculations'
        ),
        'default': True,
        'validator': bool,
    },
    'PRICING_PURCHASE_HISTORY_OVERRIDES_SUPPLIER': {
        'name': _('Purchase History Override'),
        'description': _(
            'Historical purchase order pricing overrides supplier price breaks'
        ),
        'default': False,
        'validator': bool,
    },
    'PRICING_USE_STOCK_PRICING': {
        'name': _('Use Stock Item Pricing'),
        'description': _(
            'Use pricing from manually entered stock data for pricing calculations'
        ),
        'default': True,
        'validator': bool,
    },
    'PRICING_STOCK_ITEM_AGE_DAYS': {
        'name': _('Stock Item Pricing Age'),
        'description': _(
            'Exclude stock items older than this number of days from pricing calculations'
        ),
        'default': 0,
        'units': _('days'),
        'validator': [int, MinValueValidator(0)],
    },
    'PRICING_USE_VARIANT_PRICING': {
        'name': _('Use Variant Pricing'),
        'description': _('Include variant pricing in overall pricing calculations'),
        'default': True,
        'validator': bool,
    },
    'PRICING_ACTIVE_VARIANTS': {
        'name': _('Active Variants Only'),
        'description': _(
            'Only use active variant parts for calculating variant pricing'
        ),
        'default': False,
        'validator': bool,
    },
    'PRICING_AUTO_UPDATE': {
        'name': _('Auto Update Pricing'),
        'description': _(
            'Automatically update part pricing when internal data changes'
        ),
        'default': True,
        'validator': bool,
    },
    'PRICING_UPDATE_DAYS': {
        'name': _('Pricing Rebuild Interval'),
        'description': _('Number of days before part pricing is automatically updated'),
        'units': _('days'),
        'default': 30,
        'validator': [int, MinValueValidator(0)],
    },
}
