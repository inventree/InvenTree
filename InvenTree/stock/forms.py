"""
Django Forms for interacting with Stock app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from InvenTree.forms import HelperForm

from .models import StockLocation, StockItem


class EditStockLocationForm(HelperForm):
    """ Form for editing a StockLocation """

    class Meta:
        model = StockLocation
        fields = [
            'name',
            'parent',
            'description'
        ]


class CreateStockItemForm(HelperForm):
    """ Form for creating a new StockItem """

    class Meta:
        model = StockItem
        fields = [
            'part',
            'supplier_part',
            'location',
            'quantity',
            'batch',
            'serial',
            'delete_on_deplete',
            'status',
            'notes',
            'URL',
        ]


class MoveStockItemForm(HelperForm):
    """ Form for moving a StockItem to a new location """

    note = forms.CharField(label='Notes', required=True, help_text='Add note (required)')

    class Meta:
        model = StockItem

        fields = [
            'location',
            'note'
        ]

class MoveMultipleStockItemsForm(forms.ModelForm):

    def get_location_choices(self):
        locs = StockLocation.objects.all()

        choices = [(None, '---------')]

        for loc in locs:
            choices.append((loc.pk, loc.pathstring + ' - ' + loc.description))

        return choices

    location = forms.ChoiceField(label='Destination', required=True, help_text='Destination stock location')
    note = forms.CharField(label='Notes', required=True, help_text='Add note (required)')
    # transaction = forms.BooleanField(required=False, initial=False, label='Create Transaction', help_text='Create a stock transaction for these parts')
    confirm = forms.BooleanField(required=False, initial=False, label='Confirm Stock Movement', help_text='Confirm movement of stock items')

    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)

       self.fields['location'].choices = self.get_location_choices()

    class Meta:
        model = StockItem

        fields = [
            'location',
            'note',
            # 'transaction',
            'confirm',
        ]


class StocktakeForm(forms.ModelForm):

    class Meta:
        model = StockItem

        fields = [
            'quantity',
        ]


class EditStockItemForm(HelperForm):
    """ Form for editing a StockItem object.
    Note that not all fields can be edited here (even if they can be specified during creation.
    
    location - Must be updated in a 'move' transaction
    quantity - Must be updated in a 'stocktake' transaction
    part - Cannot be edited after creation
    """

    class Meta:
        model = StockItem

        fields = [
            'supplier_part',
            'batch',
            'delete_on_deplete',
            'status',
            'notes',
            'URL',
        ]
