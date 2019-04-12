# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from InvenTree.forms import HelperForm

from .models import StockLocation, StockItem


class EditStockLocationForm(HelperForm):

    class Meta:
        model = StockLocation
        fields = [
            'name',
            'parent',
            'description'
        ]


class CreateStockItemForm(HelperForm):

    class Meta:
        model = StockItem
        fields = [
            'part',
            'supplier_part',
            'location',
            'belongs_to',
            'serial',
            'batch',
            'quantity',
            'status',
            # 'customer',
            'URL',
        ]


class MoveStockItemForm(forms.ModelForm):

    note = forms.CharField(label='Notes', required=True)

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

    class Meta:
        model = StockItem

        fields = [
            'batch',
            'status',
            'notes'
        ]