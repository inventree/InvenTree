"""User-configurable settings for the common app."""

from django.conf import settings

from moneyed import CURRENCIES


def currency_code_default():
    """Returns the default currency code (or USD if not specified)"""
    from django.db.utils import ProgrammingError

    from common.models import InvenTreeSetting

    try:
        code = InvenTreeSetting.get_setting('INVENTREE_DEFAULT_CURRENCY', create=False, cache=False)
    except ProgrammingError:  # pragma: no cover
        # database is not initialized yet
        code = ''

    if code not in CURRENCIES:
        code = 'USD'  # pragma: no cover

    return code


def currency_code_mappings():
    """Returns the current currency choices."""
    return [(a, CURRENCIES[a].name) for a in settings.CURRENCIES]


def currency_codes():
    """Returns the current currency codes."""
    return [a for a in settings.CURRENCIES]


def stock_expiry_enabled():
    """Returns True if the stock expiry feature is enabled."""
    from common.models import InvenTreeSetting

    return InvenTreeSetting.get_setting('STOCK_ENABLE_EXPIRY')
