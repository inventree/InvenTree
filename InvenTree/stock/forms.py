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


class MoveStockItemForm(forms.ModelForm):
    """ Form for moving a StockItem to a new location """

    note = forms.CharField(label='Notes', required=True, help_text='Add note (required)')

    class Meta:
        model = StockItem

        fields = [
            'location',
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
