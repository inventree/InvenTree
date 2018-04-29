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

    class Meta:
        model = StockItem

        fields = [
            'location',
        ]


class EditStockItemForm(HelperForm):

    class Meta:
        model = StockItem

        fields = [
            'quantity',
            'batch',
            'status',
        ]