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
