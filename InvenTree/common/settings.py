"""
User-configurable settings for the common app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from moneyed import CURRENCIES

from common.models import InvenTreeSetting


def currency_code_default():
    """
    Returns the default currency code (or USD if not specified)
    """

    code = InvenTreeSetting.get_setting('INVENTREE_DEFAULT_CURRENCY')

    if code not in CURRENCIES:
        code = 'USD'
    
    return code


def stock_expiry_enabled():
    """
    Returns True if the stock expiry feature is enabled
    """

    return InvenTreeSetting.get_setting('STOCK_ENABLE_EXPIRY')
