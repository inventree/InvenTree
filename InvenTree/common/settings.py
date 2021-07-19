"""
User-configurable settings for the common app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from moneyed import CURRENCIES
from django.conf import settings


def currency_code_default():
    """
    Returns the default currency code (or USD if not specified)
    """
    from django.db.utils import ProgrammingError
    from common.models import InvenTreeSetting

    try:
        code = InvenTreeSetting.get_setting('INVENTREE_DEFAULT_CURRENCY')
    except ProgrammingError:
        # database is not initialized yet
        code = ''

    if code not in CURRENCIES:
        code = 'USD'

    return code


def currency_code_mappings():
    """
    Returns the current currency choices
    """
    return [(a, CURRENCIES[a].name) for a in settings.CURRENCIES]


def currency_codes():
    """
    Returns the current currency codes
    """
    return [a for a in settings.CURRENCIES]


def stock_expiry_enabled():
    """
    Returns True if the stock expiry feature is enabled
    """
    from common.models import InvenTreeSetting

    return InvenTreeSetting.get_setting('STOCK_ENABLE_EXPIRY')
