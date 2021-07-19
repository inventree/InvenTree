"""
User-configurable settings for the common app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from moneyed import CURRENCIES
from django.conf import settings

import common.models


def currency_code_default():
    """
    Returns the default currency code (or USD if not specified)
    """

    code = common.models.InvenTreeSetting.get_setting('INVENTREE_DEFAULT_CURRENCY')

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

    return common.models.InvenTreeSetting.get_setting('STOCK_ENABLE_EXPIRY')
