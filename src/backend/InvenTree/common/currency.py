"""Helper functions for currency support."""

import logging

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from moneyed import CURRENCIES

logger = logging.getLogger('inventree')


def currency_code_default():
    """Returns the default currency code (or USD if not specified)."""
    from common.models import InvenTreeSetting

    try:
        cached_value = cache.get('currency_code_default', '')
    except Exception:
        cached_value = None

    if cached_value:
        return cached_value

    try:
        code = InvenTreeSetting.get_setting(
            'INVENTREE_DEFAULT_CURRENCY', backup_value='', create=True, cache=True
        )
    except Exception:  # pragma: no cover
        # Database may not yet be ready, no need to throw an error here
        code = ''

    if code not in CURRENCIES:
        code = 'USD'  # pragma: no cover

    # Cache the value for a short amount of time
    try:
        cache.set('currency_code_default', code, 30)
    except Exception:
        pass

    return code


def all_currency_codes() -> list:
    """Returns a list of all currency codes."""
    return [(a, CURRENCIES[a].name) for a in CURRENCIES]


def currency_codes() -> list:
    """Returns the current currency codes."""
    from common.models import InvenTreeSetting

    codes = InvenTreeSetting.get_setting('CURRENCY_CODES', 'USD', create=False)
    codes = codes.split(',')

    valid_codes = set()

    for code in codes:
        code = code.strip().upper()

        if code in CURRENCIES:
            valid_codes.add(code)
        else:
            logger.warning(f"Invalid currency code: '{code}'")

    return list(valid_codes)


def currency_code_mappings():
    """Returns the current currency choices."""
    return [(a, CURRENCIES[a].name) for a in currency_codes()]


def after_change_currency(setting):
    """Callback function when base currency is changed.

    - Update exchange rates
    - Recalculate prices for all parts
    """
    import InvenTree.ready
    import InvenTree.tasks

    if InvenTree.ready.isImportingData():
        return

    if not InvenTree.ready.canAppAccessDatabase():
        return

    from part import tasks as part_tasks

    # Immediately update exchange rates
    InvenTree.tasks.update_exchange_rates(force=True)

    # Offload update of part prices to a background task
    InvenTree.tasks.offload_task(part_tasks.check_missing_pricing, force_async=True)


def validate_currency_codes(value):
    """Validate the currency codes."""
    values = value.strip().split(',')

    valid_currencies = set()

    for code in values:
        code = code.strip().upper()

        if not code:
            continue

        if code in CURRENCIES:
            valid_currencies.add(code)
        else:
            raise ValidationError(_('Invalid currency code') + f": '{code}'")

    return list(valid_currencies)
