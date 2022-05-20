"""
Django Forms for interacting with Order objects
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from common.forms import MatchItemForm
from InvenTree.fields import InvenTreeMoneyField
from InvenTree.helpers import clean_decimal


class OrderMatchItemForm(MatchItemForm):
    """ Override MatchItemForm fields """

    def get_special_field(self, col_guess, row, file_manager):
        """ Set special fields """

        # set quantity field
        if 'quantity' in col_guess.lower():
            return forms.CharField(
                required=False,
                widget=forms.NumberInput(attrs={
                    'name': 'quantity' + str(row['index']),
                    'class': 'numberinput',
                    'type': 'number',
                    'min': '0',
                    'step': 'any',
                    'value': clean_decimal(row.get('quantity', '')),
                })
            )
        # set price field
        elif 'price' in col_guess.lower():
            return InvenTreeMoneyField(
                label=_(col_guess),
                decimal_places=5,
                max_digits=19,
                required=False,
                default_amount=clean_decimal(row.get('purchase_price', '')),
            )

        return super().get_special_field(col_guess, row, file_manager)
