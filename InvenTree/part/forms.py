"""
Django Forms for interacting with Part objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm

from django import forms

from .models import Part, PartCategory, PartAttachment
from .models import BomItem
from .models import SupplierPart


class PartImageForm(HelperForm):
    """ Form for uploading a Part image """

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


class EditPartAttachmentForm(HelperForm):
    """ Form for editing a PartAttachment object """

    class Meta:
        model = PartAttachment
        fields = [
            'part',
            'attachment',
            'comment'
        ]


class CopyPartForm(HelperForm):
    """ Form for copying a Part object. 
    In addition to direct editing of Part fields,
    the user is presented with some options for deep-copy of the Part.
    """

    copy_bom = forms.BooleanField(required=False, help_text='Copy all BOM entries for this part')
    copy_attachments = forms.BooleanField(required=False, help_text='Copy all file attachments for this part')

    class Meta:
        model = Part
        fields = [
            'copy_bom',
            'copy_attachments',
            'category',
            'name',
            'description',
            'IPN',
            'default_location',
            'units',
            'buildable',
            'consumable',
            'trackable',
            'purchaseable',
            'salable',
            'notes',
        ]


class EditPartForm(HelperForm):
    """ Form for editing a Part object """

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
    """ Form for editing a PartCategory object """

    class Meta:
        model = PartCategory
        fields = [
            'parent',
            'name',
            'description'
        ]


class EditBomItemForm(HelperForm):
    """ Form for editing a BomItem object """

    class Meta:
        model = BomItem
        fields = [
            'part',
            'sub_part',
            'quantity',
            'note'
        ]

        # Prevent editing of the part associated with this BomItem
        widgets = {'part': forms.HiddenInput()}


class EditSupplierPartForm(HelperForm):
    """ Form for editing a SupplierPart object """

    class Meta:
        model = SupplierPart
        fields = [
            'part',
            'supplier',
            'SKU',
            'description',
            'manufacturer',
            'MPN',
            'URL',
            'note',
            'single_price',
            'base_cost',
            'multiple',
            'minimum',
            'packaging',
            'lead_time'
        ]
