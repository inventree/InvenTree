"""User-configurable settings for the common app."""

import logging

from django.conf import settings

from moneyed import CURRENCIES

logger = logging.getLogger('inventree')


def currency_code_default():
    """Returns the default currency code (or USD if not specified)"""

    from common.models import InvenTreeSetting

    try:
        code = InvenTreeSetting.get_setting('INVENTREE_DEFAULT_CURRENCY', create=False, cache=False)
    except Exception:  # pragma: no cover
        # Database may not yet be ready, no need to throw an error here
        code = ''

    if code not in CURRENCIES:
        code = 'USD'  # pragma: no cover

    return code


def all_currency_codes():
    """Returns a list of all currency codes."""
    return [(a, CURRENCIES[a].name) for a in CURRENCIES]


def currency_code_mappings():
    """Returns the current currency choices."""
    return [(a, CURRENCIES[a].name) for a in settings.CURRENCIES]


def currency_codes():
    """Returns the current currency codes."""
    return list(settings.CURRENCIES)


def stock_expiry_enabled():
    """Returns True if the stock expiry feature is enabled."""
    from common.models import InvenTreeSetting

    return InvenTreeSetting.get_setting('STOCK_ENABLE_EXPIRY', False, create=False)
