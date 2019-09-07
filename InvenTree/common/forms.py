"""
Django forms for interacting with common objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm

from .models import Currency


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
