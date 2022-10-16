"""Django Forms for interacting with Part objects."""

from django import forms
from django.utils.translation import gettext_lazy as _

from common.forms import MatchItemForm
from InvenTree.helpers import clean_decimal

from .models import Part


class BomMatchItemForm(MatchItemForm):
    """Override MatchItemForm fields."""

    def get_special_field(self, col_guess, row, file_manager):
        """Set special fields."""
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

        return super().get_special_field(col_guess, row, file_manager)


class PartPriceForm(forms.Form):
    """Simple form for viewing part pricing information."""

    quantity = forms.IntegerField(
        required=True,
        initial=1,
        label=_('Quantity'),
        help_text=_('Input quantity for price calculation')
    )

    class Meta:
        """Metaclass defines fields for this form"""
        model = Part
        fields = [
            'quantity',
        ]
