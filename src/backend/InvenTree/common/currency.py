"""Helper functions for currency support."""

import decimal
import math
from typing import Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import structlog
from moneyed import CURRENCIES

import InvenTree.helpers
import InvenTree.ready

logger = structlog.get_logger('inventree')


def currency_code_default(create: bool = True):
    """Returns the default currency code (or USD if not specified)."""
    from common.settings import get_global_setting

    code = ''

    if InvenTree.ready.isAppLoaded('common'):
        try:
            code = get_global_setting(
                'INVENTREE_DEFAULT_CURRENCY', create=create, cache=True
            )
        except Exception:  # pragma: no cover
            # Database may not yet be ready, no need to throw an error here
            code = ''

    if not code or code not in CURRENCIES:
        code = 'USD'  # pragma: no cover

    return code


def all_currency_codes() -> list:
    """Returns a list of all currency codes."""
    return [(a, CURRENCIES[a].name) for a in CURRENCIES]


def currency_codes_default_list() -> str:
    """Return a comma-separated list of default currency codes."""
    return 'AUD,CAD,CNY,EUR,GBP,JPY,NZD,USD'


def currency_codes() -> list:
    """Returns the current currency codes."""
    from common.settings import get_global_setting

    codes = None

    # Ensure we do not hit the database until the common app is loaded
    if InvenTree.ready.isAppLoaded('common'):
        codes = get_global_setting(
            'CURRENCY_CODES', create=False, environment_key='INVENTREE_CURRENCY_CODES'
        ).strip()

    if not codes:
        codes = currency_codes_default_list()

    codes = codes.split(',')

    valid_codes = []

    for code in codes:
        code = code.strip().upper()

        if code in valid_codes:
            continue

        if code in CURRENCIES:
            valid_codes.append(code)
        else:
            logger.warning(f"Invalid currency code: '{code}'")

    if len(valid_codes) == 0:
        valid_codes = list(currency_codes_default_list().split(','))

    return valid_codes


def currency_code_mappings() -> list:
    """Returns the current currency choices."""
    return [(a, f'{a} - {CURRENCIES[a].name}') for a in currency_codes()]


def after_change_currency(setting) -> None:
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
    InvenTree.tasks.offload_task(
        part_tasks.check_missing_pricing, force_async=True, group='pricing'
    )


def validate_currency_codes(value):
    """Validate the currency codes."""
    values = value.strip().split(',')

    valid_currencies = set()

    for code in values:
        code = code.strip().upper()

        if not code:
            continue

        if code not in CURRENCIES:
            raise ValidationError(_('Invalid currency code') + f": '{code}'")
        elif code in valid_currencies:
            raise ValidationError(_('Duplicate currency code') + f": '{code}'")
        else:
            valid_currencies.add(code)

    if len(valid_currencies) == 0:
        raise ValidationError(_('No valid currency codes provided'))

    return list(valid_currencies)


def currency_exchange_plugins() -> Optional[list]:
    """Return a list of plugin choices which can be used for currency exchange."""
    try:
        from plugin import PluginMixinEnum, registry

        plugs = registry.with_mixin(PluginMixinEnum.CURRENCY_EXCHANGE, active=True)
    except Exception:
        plugs = []

    if len(plugs) == 0:
        return None

    return [('', _('No plugin'))] + [(plug.slug, plug.human_name) for plug in plugs]


def get_price(
    instance,
    quantity,
    moq=True,
    multiples=True,
    currency=None,
    break_name: str = 'price_breaks',
):
    """Calculate the price based on quantity price breaks.

    - Don't forget to add in flat-fee cost (base_cost field)
    - If MOQ (minimum order quantity) is required, bump quantity
    - If order multiples are to be observed, then we need to calculate based on that, too
    """
    # from common.currency import currency_code_default

    if hasattr(instance, break_name):
        price_breaks = getattr(instance, break_name).all()
    else:
        price_breaks = []

    # No price break information available?
    if len(price_breaks) == 0:
        return None

    # Check if quantity is fraction and disable multiples
    multiples = quantity % 1 == 0

    # Order multiples
    if multiples:
        quantity = int(math.ceil(quantity / instance.multiple) * instance.multiple)

    pb_found = False
    pb_quantity = -1
    pb_cost = 0.0

    if currency is None:
        # Default currency selection
        currency = currency_code_default()

    pb_min = None
    for pb in price_breaks:
        # Store smallest price break
        if not pb_min:
            pb_min = pb

        # Ignore this pricebreak (quantity is too high)
        if pb.quantity > quantity:
            continue

        pb_found = True

        # If this price-break quantity is the largest so far, use it!
        if pb.quantity > pb_quantity:
            pb_quantity = pb.quantity

            # Convert everything to the selected currency
            pb_cost = pb.convert_to(currency)

    # Use smallest price break
    if not pb_found and pb_min:
        # Update price break information
        pb_quantity = pb_min.quantity
        pb_cost = pb_min.convert_to(currency)
        # Trigger cost calculation using smallest price break
        pb_found = True

    # Convert quantity to decimal.Decimal format
    quantity = decimal.Decimal(f'{quantity}')

    if pb_found:
        cost = pb_cost * quantity
        return InvenTree.helpers.normalize(cost + instance.base_cost)
    return None
