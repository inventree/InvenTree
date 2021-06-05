"""
User-configurable settings for the common app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from moneyed import CURRENCIES

import common.models
from django.conf import settings


def currency_code_default():
    """
    Returns the default currency code (or USD if not specified)
    """

    code = settings.BASE_CURRENCY

    if code not in CURRENCIES:
        code = 'USD'

    return code


def stock_expiry_enabled():
    """
    Returns True if the stock expiry feature is enabled
    """

    return common.models.InvenTreeSetting.get_setting('STOCK_ENABLE_EXPIRY')
