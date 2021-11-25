"""
Django Forms for interacting with Part objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from mptt.fields import TreeNodeChoiceField

from InvenTree.forms import HelperForm
from InvenTree.helpers import GetExportFormats, clean_decimal
from InvenTree.fields import RoundingDecimalFormField

import common.models
from common.forms import MatchItemForm

from .models import Part, PartCategory, PartRelated
from .models import PartParameterTemplate
from .models import PartCategoryParameterTemplate
from .models import PartSellPriceBreak, PartInternalPriceBreak


class PartModelChoiceField(forms.ModelChoiceField):
    """ Extending string representation of Part instance with available stock """

    def label_from_instance(self, part):

        label = str(part)

        # Optionally display available part quantity
        if common.models.InvenTreeSetting.get_setting('PART_SHOW_QUANTITY_IN_FORMS'):
            label += f" - {part.available_stock}"

        return label


class PartImageDownloadForm(HelperForm):
    """
    Form for downloading an image from a URL
    """

    url = forms.URLField(
        label=_('URL'),
        help_text=_('Image URL'),
        required=True,
    )

    class Meta:
        model = Part
        fields = [
            'url',
        ]


class BomExportForm(forms.Form):
    """ Simple form to let user set BOM export options,
    before exporting a BOM (bill of materials) file.
    """

    file_format = forms.ChoiceField(label=_("File Format"), help_text=_("Select output file format"))

    cascading = forms.BooleanField(label=_("Cascading"), required=False, initial=True, help_text=_("Download cascading / multi-level BOM"))

    levels = forms.IntegerField(label=_("Levels"), required=True, initial=0, help_text=_("Select maximum number of BOM levels to export (0 = all levels)"))

    parameter_data = forms.BooleanField(label=_("Include Parameter Data"), required=False, initial=False, help_text=_("Include part parameters data in exported BOM"))

    stock_data = forms.BooleanField(label=_("Include Stock Data"), required=False, initial=False, help_text=_("Include part stock data in exported BOM"))

    manufacturer_data = forms.BooleanField(label=_("Include Manufacturer Data"), required=False, initial=True, help_text=_("Include part manufacturer data in exported BOM"))

    supplier_data = forms.BooleanField(label=_("Include Supplier Data"), required=False, initial=True, help_text=_("Include part supplier data in exported BOM"))

    def get_choices(self):
        """ BOM export format choices """

        return [(x, x.upper()) for x in GetExportFormats()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['file_format'].choices = self.get_choices()


class BomDuplicateForm(HelperForm):
    """
    Simple confirmation form for BOM duplication.

    Select which parent to select from.
    """

    parent = PartModelChoiceField(
        label=_('Parent Part'),
        help_text=_('Select parent part to copy BOM from'),
        queryset=Part.objects.filter(is_template=True),
    )

    clear = forms.BooleanField(
        required=False, initial=True,
        help_text=_('Clear existing BOM items')
    )

    confirm = forms.BooleanField(
        required=False, initial=False,
        label=_('Confirm'),
        help_text=_('Confirm BOM duplication')
    )

    class Meta:
        model = Part
        fields = [
            'parent',
            'clear',
            'confirm',
        ]


class BomValidateForm(HelperForm):
    """ Simple confirmation form for BOM validation.
    User is presented with a single checkbox input,
    to confirm that the BOM for this part is valid
    """

    validate = forms.BooleanField(required=False, initial=False, label=_('validate'), help_text=_('Confirm that the BOM is correct'))

    class Meta:
        model = Part
        fields = [
            'validate'
        ]


class BomMatchItemForm(MatchItemForm):
    """ Override MatchItemForm fields """

    def get_special_field(self, col_guess, row, file_manager):
        """ Set special fields """

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

        # return default
        return super().get_special_field(col_guess, row, file_manager)


class SetPartCategoryForm(forms.Form):
    """ Form for setting the category of multiple Part objects """

    part_category = TreeNodeChoiceField(queryset=PartCategory.objects.all(), required=True, help_text=_('Select part category'))


class EditPartParameterTemplateForm(HelperForm):
    """ Form for editing a PartParameterTemplate object """

    class Meta:
        model = PartParameterTemplate
        fields = [
            'name',
            'units'
        ]


class EditCategoryForm(HelperForm):
    """ Form for editing a PartCategory object """

    field_prefix = {
        'default_keywords': 'fa-key',
    }

    class Meta:
        model = PartCategory
        fields = [
            'parent',
            'name',
            'description',
            'default_location',
            'default_keywords',
        ]


class EditCategoryParameterTemplateForm(HelperForm):
    """ Form for editing a PartCategoryParameterTemplate object """

    add_to_same_level_categories = forms.BooleanField(required=False,
                                                      initial=False,
                                                      help_text=_('Add parameter template to same level categories'))

    add_to_all_categories = forms.BooleanField(required=False,
                                               initial=False,
                                               help_text=_('Add parameter template to all categories'))

    class Meta:
        model = PartCategoryParameterTemplate
        fields = [
            'category',
            'parameter_template',
            'default_value',
            'add_to_same_level_categories',
            'add_to_all_categories',
        ]


class PartPriceForm(forms.Form):
    """ Simple form for viewing part pricing information """

    quantity = forms.IntegerField(
        required=True,
        initial=1,
        label=_('Quantity'),
        help_text=_('Input quantity for price calculation')
    )

    class Meta:
        model = Part
        fields = [
            'quantity',
        ]


class EditPartSalePriceBreakForm(HelperForm):
    """
    Form for creating / editing a sale price for a part
    """

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5, label=_('Quantity'))

    class Meta:
        model = PartSellPriceBreak
        fields = [
            'part',
            'quantity',
            'price',
        ]


class EditPartInternalPriceBreakForm(HelperForm):
    """
    Form for creating / editing a internal price for a part
    """

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5, label=_('Quantity'))

    class Meta:
        model = PartInternalPriceBreak
        fields = [
            'part',
            'quantity',
            'price',
        ]
