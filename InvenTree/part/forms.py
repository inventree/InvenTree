# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm

from .models import Part, PartCategory, BomItem
from .models import SupplierPart


class PartImageForm(HelperForm):

    class Meta:
        model = Part
        fields = [
            'image',
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
            'minimum_stock',
            'buildable',
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
            'quantity'
        ]


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
            ]
