"""
Django Forms for interacting with Stock app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.forms.utils import ErrorDict
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from mptt.fields import TreeNodeChoiceField

from InvenTree.forms import HelperForm
from InvenTree.fields import RoundingDecimalFormField
from InvenTree.fields import DatePickerFormField

from report.models import TestReport

from part.models import Part

from .models import StockLocation, StockItem, StockItemTracking


class AssignStockItemToCustomerForm(HelperForm):
    """
    Form for manually assigning a StockItem to a Customer
    """

    class Meta:
        model = StockItem
        fields = [
            'customer',
        ]


class ReturnStockItemForm(HelperForm):
    """
    Form for manually returning a StockItem into stock
    """

    class Meta:
        model = StockItem
        fields = [
            'location',
        ]


class EditStockLocationForm(HelperForm):
    """ Form for editing a StockLocation """

    class Meta:
        model = StockLocation
        fields = [
            'name',
            'parent',
            'description',
            'owner',
        ]


class ConvertStockItemForm(HelperForm):
    """
    Form for converting a StockItem to a variant of its current part.
    """

    class Meta:
        model = StockItem
        fields = [
            'part'
        ]


class CreateStockItemForm(HelperForm):
    """ Form for creating a new StockItem """

    expiry_date = DatePickerFormField(
        label=_('Expiry Date'),
        help_text=_('Expiration date for this stock item'),
    )

    serial_numbers = forms.CharField(label=_('Serial Numbers'), required=False, help_text=_('Enter unique serial numbers (or leave blank)'))

    def __init__(self, *args, **kwargs):

        self.field_prefix = {
            'serial_numbers': 'fa-hashtag',
            'link': 'fa-link',
        }

        super().__init__(*args, **kwargs)

    class Meta:
        model = StockItem
        fields = [
            'part',
            'supplier_part',
            'location',
            'quantity',
            'batch',
            'serial_numbers',
            'packaging',
            'purchase_price',
            'expiry_date',
            'link',
            'delete_on_deplete',
            'status',
            'owner',
        ]

    # Custom clean to prevent complex StockItem.clean() logic from running (yet)
    def full_clean(self):
        self._errors = ErrorDict()

        if not self.is_bound:  # Stop further processing.
            return

        self.cleaned_data = {}

        # If the form is permitted to be empty, and none of the form data has
        # changed from the initial data, short circuit any validation.
        if self.empty_permitted and not self.has_changed():
            return

        # Don't run _post_clean() as this will run StockItem.clean()
        self._clean_fields()
        self._clean_form()


class SerializeStockForm(HelperForm):
    """ Form for serializing a StockItem. """

    destination = TreeNodeChoiceField(queryset=StockLocation.objects.all(), label=_('Destination'), required=True, help_text=_('Destination for serialized stock (by default, will remain in current location)'))

    serial_numbers = forms.CharField(label=_('Serial numbers'), required=True, help_text=_('Unique serial numbers (must match quantity)'))

    note = forms.CharField(label=_('Notes'), required=False, help_text=_('Add transaction note (optional)'))

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5, label=_('Quantity'))

    def __init__(self, *args, **kwargs):

        # Extract the stock item
        item = kwargs.pop('item', None)

        if item:
            self.field_placeholder['serial_numbers'] = item.part.getSerialNumberString(item.quantity)

        super().__init__(*args, **kwargs)

    class Meta:
        model = StockItem

        fields = [
            'quantity',
            'serial_numbers',
            'destination',
            'note',
        ]


class StockItemLabelSelectForm(HelperForm):
    """ Form for selecting a label template for a StockItem """

    label = forms.ChoiceField(
        label=_('Label'),
        help_text=_('Select test report template')
    )

    class Meta:
        model = StockItem
        fields = [
            'label',
        ]

    def get_label_choices(self, labels):

        choices = []

        if len(labels) > 0:
            for label in labels:
                choices.append((label.pk, label))

        return choices

    def __init__(self, labels, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['label'].choices = self.get_label_choices(labels)


class TestReportFormatForm(HelperForm):
    """ Form for selection a test report template """

    class Meta:
        model = StockItem
        fields = [
            'template',
        ]

    def __init__(self, stock_item, *args, **kwargs):
        self.stock_item = stock_item

        super().__init__(*args, **kwargs)
        self.fields['template'].choices = self.get_template_choices()

    def get_template_choices(self):
        """
        Generate a list of of TestReport options for the StockItem
        """

        choices = []

        templates = TestReport.objects.filter(enabled=True)

        for template in templates:
            if template.enabled and template.matches_stock_item(self.stock_item):
                choices.append((template.pk, template))

        return choices

    template = forms.ChoiceField(label=_('Template'), help_text=_('Select test report template'))


class InstallStockForm(HelperForm):
    """
    Form for manually installing a stock item into another stock item
    """

    part = forms.ModelChoiceField(
        queryset=Part.objects.all(),
        widget=forms.HiddenInput()
    )

    stock_item = forms.ModelChoiceField(
        required=True,
        queryset=StockItem.objects.filter(StockItem.IN_STOCK_FILTER),
        help_text=_('Stock item to install')
    )

    to_install = forms.BooleanField(
        widget=forms.HiddenInput(),
        required=False,
    )

    notes = forms.CharField(
        required=False,
        help_text=_('Notes')
    )

    class Meta:
        model = StockItem
        fields = [
            'part',
            'stock_item',
            # 'quantity_to_install',
            'notes',
        ]

    def clean(self):

        data = super().clean()

        stock_item = data.get('stock_item', None)
        quantity = data.get('quantity_to_install', None)

        if stock_item and quantity and quantity > stock_item.quantity:
            raise ValidationError({'quantity_to_install': _('Must not exceed available quantity')})

        return data


class UninstallStockForm(forms.ModelForm):
    """
    Form for uninstalling a stock item which is installed in another item.
    """

    location = TreeNodeChoiceField(queryset=StockLocation.objects.all(), label=_('Location'), help_text=_('Destination location for uninstalled items'))

    note = forms.CharField(label=_('Notes'), required=False, help_text=_('Add transaction note (optional)'))

    confirm = forms.BooleanField(required=False, initial=False, label=_('Confirm uninstall'), help_text=_('Confirm removal of installed stock items'))

    class Meta:

        model = StockItem

        fields = [
            'location',
            'note',
            'confirm',
        ]


class EditStockItemForm(HelperForm):
    """ Form for editing a StockItem object.
    Note that not all fields can be edited here (even if they can be specified during creation.

    location - Must be updated in a 'move' transaction
    quantity - Must be updated in a 'stocktake' transaction
    part - Cannot be edited after creation
    """

    expiry_date = DatePickerFormField(
        label=_('Expiry Date'),
        help_text=_('Expiration date for this stock item'),
    )

    class Meta:
        model = StockItem

        fields = [
            'supplier_part',
            'serial',
            'batch',
            'status',
            'expiry_date',
            'purchase_price',
            'packaging',
            'link',
            'delete_on_deplete',
            'owner',
        ]


class TrackingEntryForm(HelperForm):
    """
    Form for creating / editing a StockItemTracking object.

    Note: 2021-05-11 - This form is not currently used - should delete?
    """

    class Meta:
        model = StockItemTracking

        fields = [
            'notes',
        ]
