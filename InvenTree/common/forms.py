"""
Django forms for interacting with common objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm

from .models import Currency, InvenTreeSetting


class CurrencyEditForm(HelperForm):
    """ Form for creating / editing a currency object """

    class Meta:
        model = Currency
        fields = [
            'symbol',
            'suffix',
            'description',
            'value',
            'base'
        ]


class SettingEditForm(HelperForm):
    """
    Form for creating / editing a settings object
    """

    class Meta:
        model = InvenTreeSetting

        fields = [
            'key',
            'value'
        ]
