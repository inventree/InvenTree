"""
Django Forms for interacting with Stock app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.forms.utils import ErrorDict
from django.utils.translation import ugettext as _

from mptt.fields import TreeNodeChoiceField

from InvenTree.helpers import GetExportFormats
from InvenTree.forms import HelperForm
from InvenTree.fields import RoundingDecimalFormField

from report.models import TestReport

from .models import StockLocation, StockItem, StockItemTracking
from .models import StockItemAttachment
from .models import StockItemTestResult


class EditStockItemAttachmentForm(HelperForm):
    """
    Form for creating / editing a StockItemAttachment object
    """

    class Meta:
        model = StockItemAttachment
        fields = [
            'stock_item',
            'attachment',
            'comment'
        ]


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


class EditStockItemTestResultForm(HelperForm):
    """
    Form for creating / editing a StockItemTestResult object.
    """

    class Meta:
        model = StockItemTestResult
        fields = [
            'stock_item',
            'test',
            'result',
            'value',
            'attachment',
            'notes',
        ]


class EditStockLocationForm(HelperForm):
    """ Form for editing a StockLocation """

    class Meta:
        model = StockLocation
        fields = [
            'name',
            'parent',
            'description'
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

    serial_numbers = forms.CharField(label='Serial numbers', required=False, help_text=_('Enter unique serial numbers (or leave blank)'))

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
            'link',
            'delete_on_deplete',
            'status',
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

    destination = TreeNodeChoiceField(queryset=StockLocation.objects.all(), label='Destination', required=True, help_text='Destination for serialized stock (by default, will remain in current location)')
    
    serial_numbers = forms.CharField(label='Serial numbers', required=True, help_text='Unique serial numbers (must match quantity)')
    
    note = forms.CharField(label='Notes', required=False, help_text='Add transaction note (optional)')

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5)

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
            if template.matches_stock_item(self.stock_item):
                choices.append((template.pk, template))

        return choices

    template = forms.ChoiceField(label=_('Template'), help_text=_('Select test report template'))


class ExportOptionsForm(HelperForm):
    """ Form for selecting stock export options """

    file_format = forms.ChoiceField(label=_('File Format'), help_text=_('Select output file format'))

    include_sublocations = forms.BooleanField(required=False, initial=True, help_text=_("Include stock items in sub locations"))

    class Meta:
        model = StockLocation
        fields = [
            'file_format',
            'include_sublocations',
        ]

    def get_format_choices(self):
        """ File format choices """

        choices = [(x, x.upper()) for x in GetExportFormats()]

        return choices

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['file_format'].choices = self.get_format_choices()


class AdjustStockForm(forms.ModelForm):
    """ Form for performing simple stock adjustments.

    - Add stock
    - Remove stock
    - Count stock
    - Move stock

    This form is used for managing stock adjuments for single or multiple stock items.
    """

    destination = TreeNodeChoiceField(queryset=StockLocation.objects.all(), label='Destination', required=True, help_text=_('Destination stock location'))
    
    note = forms.CharField(label='Notes', required=True, help_text='Add note (required)')
    
    # transaction = forms.BooleanField(required=False, initial=False, label='Create Transaction', help_text='Create a stock transaction for these parts')
    
    confirm = forms.BooleanField(required=False, initial=False, label='Confirm stock adjustment', help_text=_('Confirm movement of stock items'))

    set_loc = forms.BooleanField(required=False, initial=False, label='Set Default Location', help_text=_('Set the destination as the default location for selected parts'))

    class Meta:
        model = StockItem

        fields = [
            'destination',
            'note',
            # 'transaction',
            'confirm',
        ]


class EditStockItemForm(HelperForm):
    """ Form for editing a StockItem object.
    Note that not all fields can be edited here (even if they can be specified during creation.
    
    location - Must be updated in a 'move' transaction
    quantity - Must be updated in a 'stocktake' transaction
    part - Cannot be edited after creation
    """

    class Meta:
        model = StockItem

        fields = [
            'supplier_part',
            'serial',
            'batch',
            'status',
            'link',
            'delete_on_deplete',
        ]


class TrackingEntryForm(HelperForm):
    """ Form for creating / editing a StockItemTracking object.
    """

    class Meta:
        model = StockItemTracking

        fields = [
            'title',
            'notes',
            'link',
        ]
