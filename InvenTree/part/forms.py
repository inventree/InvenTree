# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm

from django import forms

from .models import Part, PartCategory, BomItem
from .models import SupplierPart


class PartImageForm(HelperForm):

    class Meta:
        model = Part
        fields = [
            'image',
        ]


class BomExportForm(HelperForm):

    # TODO - Define these choices somewhere else, and import them here
    format_choices = (
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
        ('xml', 'XML'),
        ('xlsx', 'XLSX'),
        ('html', 'HTML')
    )

    # Select export type
    format = forms.CharField(label='Format', widget=forms.Select(choices=format_choices), required='true', help_text='Select export format')

    class Meta:
        model = Part
        fields = [
            'format',
        ]


class EditPartForm(HelperForm):

    class Meta:
        model = Part
        fields = [
            'category',
            'name',
            'description',
            'IPN',
            'URL',
            'default_location',
            'default_supplier',
            'units',
            'minimum_stock',
            'buildable',
            'consumable',
            'trackable',
            'purchaseable',
            'salable',
            'notes',
            'image',
        ]


class EditCategoryForm(HelperForm):

    class Meta:
        model = PartCategory
        fields = [
            'parent',
            'name',
            'description'
        ]


class EditBomItemForm(HelperForm):

    class Meta:
        model = BomItem
        fields = [
            'part',
            'sub_part',
            'quantity',
            'note'
        ]
        widgets = {'part': forms.HiddenInput()}


class EditSupplierPartForm(HelperForm):

        class Meta:
            model = SupplierPart
            fields = [
                'supplier',
                'SKU',
                'part',
                'description',
                'URL',
                'manufacturer',
                'MPN',
                'note',
                'single_price',
                'base_cost',
                'multiple',
                'minimum',
                'packaging',
                'lead_time'
            ]
