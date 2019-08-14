"""
Django Forms for interacting with Part objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm

from django import forms
from django.core.validators import MinValueValidator

from .models import Part, PartCategory, PartAttachment
from .models import BomItem


class PartImageForm(HelperForm):
    """ Form for uploading a Part image """

    class Meta:
        model = Part
        fields = [
            'image',
        ]


class BomValidateForm(HelperForm):
    """ Simple confirmation form for BOM validation.
    User is presented with a single checkbox input,
    to confirm that the BOM for this part is valid
    """

    validate = forms.BooleanField(required=False, initial=False, help_text='Confirm that the BOM is correct')

    class Meta:
        model = Part
        fields = [
            'validate'
        ]


class BomUploadSelectFile(HelperForm):
    """ Form for importing a BOM. Provides a file input box for upload """

    bom_file = forms.FileField(label='BOM file', required=True, help_text="Select BOM file to upload")

    class Meta:
        model = Part
        fields = [
            'bom_file',
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


class EditPartForm(HelperForm):
    """ Form for editing a Part object """

    deep_copy = forms.BooleanField(required=False,
                                   initial=True,
                                   help_text="Perform 'deep copy' which will duplicate all BOM data for this part",
                                   widget=forms.HiddenInput())

    confirm_creation = forms.BooleanField(required=False,
                                          initial=False,
                                          help_text='Confirm part creation',
                                          widget=forms.HiddenInput())

    class Meta:
        model = Part
        fields = [
            'deep_copy',
            'confirm_creation',
            'category',
            'name',
            'IPN',
            'description',
            'revision',
            'keywords',
            'variant_of',
            'is_template',
            'URL',
            'default_location',
            'default_supplier',
            'units',
            'minimum_stock',
            'notes',
            'active',
        ]


class EditCategoryForm(HelperForm):
    """ Form for editing a PartCategory object """

    class Meta:
        model = PartCategory
        fields = [
            'parent',
            'name',
            'description',
            'default_location',
            'default_keywords',
        ]


class EditBomItemForm(HelperForm):
    """ Form for editing a BomItem object """

    class Meta:
        model = BomItem
        fields = [
            'part',
            'sub_part',
            'quantity',
            'reference',
            'overage',
            'note'
        ]

        # Prevent editing of the part associated with this BomItem
        widgets = {'part': forms.HiddenInput()}


class PartPriceForm(forms.Form):
    """ Simple form for viewing part pricing information """

    quantity = forms.IntegerField(
        required=True,
        initial=1,
        help_text='Input quantity for price calculation'
    )

    class Meta:
        model = Part
        fields = [
            'quantity'
        ]
