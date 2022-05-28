"""Django Forms for interacting with Part objects."""

from django import forms
from django.utils.translation import gettext_lazy as _

from mptt.fields import TreeNodeChoiceField

import common.models
from common.forms import MatchItemForm
from InvenTree.fields import RoundingDecimalFormField
from InvenTree.forms import HelperForm
from InvenTree.helpers import clean_decimal

from .models import (Part, PartCategory, PartCategoryParameterTemplate,
                     PartInternalPriceBreak, PartParameterTemplate,
                     PartSellPriceBreak)


class PartModelChoiceField(forms.ModelChoiceField):
    """Extending string representation of Part instance with available stock."""

    def label_from_instance(self, part):

        label = str(part)

        # Optionally display available part quantity
        if common.models.InvenTreeSetting.get_setting('PART_SHOW_QUANTITY_IN_FORMS'):
            label += f" - {part.available_stock}"

        return label


class PartImageDownloadForm(HelperForm):
    """Form for downloading an image from a URL."""

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


class BomMatchItemForm(MatchItemForm):
    """Override MatchItemForm fields."""

    def get_special_field(self, col_guess, row, file_manager):
        """Set special fields."""
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

        return super().get_special_field(col_guess, row, file_manager)


class SetPartCategoryForm(forms.Form):
    """Form for setting the category of multiple Part objects."""

    part_category = TreeNodeChoiceField(queryset=PartCategory.objects.all(), required=True, help_text=_('Select part category'))


class EditPartParameterTemplateForm(HelperForm):
    """Form for editing a PartParameterTemplate object."""

    class Meta:
        model = PartParameterTemplate
        fields = [
            'name',
            'units'
        ]


class EditCategoryParameterTemplateForm(HelperForm):
    """Form for editing a PartCategoryParameterTemplate object."""

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
    """Simple form for viewing part pricing information."""

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
    """Form for creating / editing a sale price for a part."""

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5, label=_('Quantity'))

    class Meta:
        model = PartSellPriceBreak
        fields = [
            'part',
            'quantity',
            'price',
        ]


class EditPartInternalPriceBreakForm(HelperForm):
    """Form for creating / editing a internal price for a part."""

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5, label=_('Quantity'))

    class Meta:
        model = PartInternalPriceBreak
        fields = [
            'part',
            'quantity',
            'price',
        ]
