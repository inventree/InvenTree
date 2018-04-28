# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from crispy_forms.helper import FormHelper

from .models import StockLocation, StockItem


class EditStockLocationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EditStockLocationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False

        initial = kwargs.get('initial', {})

        if 'location' in initial:
            self.fields['parent'].disabled = True

    class Meta:
        model = StockLocation
        fields = [
            'name',
            'parent',
            'description'
        ]


class EditStockItemForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EditStockItemForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False

        initial = kwargs.get('initial', {})

        for field in ['part', 'location']:
            if field in initial:
                self.fields[field].disabled = True

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
