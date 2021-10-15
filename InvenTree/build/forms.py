"""
Django Forms for interacting with Build objects
"""

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django import forms

from InvenTree.forms import HelperForm
from InvenTree.fields import RoundingDecimalFormField
from InvenTree.fields import DatePickerFormField

from InvenTree.status_codes import StockStatus

from .models import Build

from stock.models import StockLocation, StockItem


class EditBuildForm(HelperForm):
    """ Form for editing a Build object.
    """

    field_prefix = {
        'reference': 'BO',
        'link': 'fa-link',
        'batch': 'fa-layer-group',
        'serial-numbers': 'fa-hashtag',
        'location': 'fa-map-marker-alt',
        'target_date': 'fa-calendar-alt',
    }

    field_placeholder = {
        'reference': _('Build Order reference'),
        'target_date': _('Order target date'),
    }

    target_date = DatePickerFormField(
        label=_('Target Date'),
        help_text=_('Target date for build completion. Build will be overdue after this date.')
    )

    quantity = RoundingDecimalFormField(
        max_digits=10, decimal_places=5,
        label=_('Quantity'),
        help_text=_('Number of items to build')
    )

    class Meta:
        model = Build
        fields = [
            'reference',
            'title',
            'part',
            'quantity',
            'batch',
            'target_date',
            'take_from',
            'destination',
            'parent',
            'sales_order',
            'link',
            'issued_by',
            'responsible',
        ]


class BuildOutputCreateForm(HelperForm):
    """
    Form for creating a new build output.
    """

    def __init__(self, *args, **kwargs):

        build = kwargs.pop('build', None)

        if build:
            self.field_placeholder['serial_numbers'] = build.part.getSerialNumberString()

        super().__init__(*args, **kwargs)

    field_prefix = {
        'serial_numbers': 'fa-hashtag',
    }

    output_quantity = forms.IntegerField(
        label=_('Quantity'),
        help_text=_('Enter quantity for build output'),
    )

    serial_numbers = forms.CharField(
        label=_('Serial Numbers'),
        required=False,
        help_text=_('Enter serial numbers for build outputs'),
    )

    confirm = forms.BooleanField(
        required=True,
        label=_('Confirm'),
        help_text=_('Confirm creation of build output'),
    )

    class Meta:
        model = Build
        fields = [
            'output_quantity',
            'batch',
            'serial_numbers',
            'confirm',
        ]


class BuildOutputDeleteForm(HelperForm):
    """
    Form for deleting a build output.
    """

    confirm = forms.BooleanField(
        required=False,
        label=_('Confirm'),
        help_text=_('Confirm deletion of build output')
    )

    output_id = forms.IntegerField(
        required=True,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Build
        fields = [
            'confirm',
            'output_id',
        ]


class CompleteBuildForm(HelperForm):
    """
    Form for marking a build as complete
    """

    confirm = forms.BooleanField(
        required=True,
        label=_('Confirm'),
        help_text=_('Mark build as complete'),
    )

    class Meta:
        model = Build
        fields = [
            'confirm',
        ]


class CompleteBuildOutputForm(HelperForm):
    """
    Form for completing a single build output
    """

    field_prefix = {
        'serial_numbers': 'fa-hashtag',
    }

    field_placeholder = {
    }

    location = forms.ModelChoiceField(
        queryset=StockLocation.objects.all(),
        label=_('Location'),
        help_text=_('Location of completed parts'),
    )

    stock_status = forms.ChoiceField(
        label=_('Status'),
        help_text=_('Build output stock status'),
        initial=StockStatus.OK,
        choices=StockStatus.items(),
    )

    confirm_incomplete = forms.BooleanField(
        required=False,
        label=_('Confirm incomplete'),
        help_text=_("Confirm completion with incomplete stock allocation")
    )

    confirm = forms.BooleanField(required=True, label=_('Confirm'), help_text=_('Confirm build completion'))

    output = forms.ModelChoiceField(
        queryset=StockItem.objects.all(),  # Queryset is narrowed in the view
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Build
        fields = [
            'location',
            'output',
            'stock_status',
            'confirm',
            'confirm_incomplete',
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)


class CancelBuildForm(HelperForm):
    """ Form for cancelling a build """

    confirm_cancel = forms.BooleanField(required=False, label=_('Confirm cancel'), help_text=_('Confirm build cancellation'))

    class Meta:
        model = Build
        fields = [
            'confirm_cancel'
        ]
