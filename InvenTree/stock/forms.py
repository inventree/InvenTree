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
from .models import StockLocation, StockItem, StockItemTracking


class EditStockLocationForm(HelperForm):
    """ Form for editing a StockLocation """

    class Meta:
        model = StockLocation
        fields = [
            'name',
            'parent',
            'description'
        ]


class CreateStockItemForm(HelperForm):
    """ Form for creating a new StockItem """

    serial_numbers = forms.CharField(label='Serial numbers', required=False, help_text=_('Enter unique serial numbers (or leave blank)'))

    class Meta:
        model = StockItem
        fields = [
            'part',
            'supplier_part',
            'location',
            'quantity',
            'batch',
            'serial_numbers',
            'delete_on_deplete',
            'status',
            'notes',
            'URL',
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


class SerializeStockForm(forms.ModelForm):
    """ Form for serializing a StockItem. """

    destination = TreeNodeChoiceField(queryset=StockLocation.objects.all(), label='Destination', required=True, help_text='Destination for serialized stock (by default, will remain in current location)')
    
    serial_numbers = forms.CharField(label='Serial numbers', required=True, help_text='Unique serial numbers (must match quantity)')
    
    note = forms.CharField(label='Notes', required=False, help_text='Add transaction note (optional)')

    class Meta:
        model = StockItem

        fields = [
            'quantity',
            'serial_numbers',
            'destination',
            'note',
        ]


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
            'notes',
            'URL',
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
            'URL',
        ]
