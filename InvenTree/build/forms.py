"""
Django Forms for interacting with Build objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from InvenTree.forms import HelperForm
from InvenTree.fields import RoundingDecimalFormField

from django import forms
from .models import Build, BuildItem, BuildOrderAttachment
from stock.models import StockLocation


class EditBuildForm(HelperForm):
    """ Form for editing a Build object.
    """

    field_prefix = {
        'reference': 'BO',
        'link': 'fa-link',
        'batch': 'fa-layer-group',
        'location': 'fa-map-marker-alt',
    }

    field_placeholder = {
        'reference': _('Build Order reference')
    }

    class Meta:
        model = Build
        fields = [
            'reference',
            'title',
            'part',
            'quantity',
            'batch',
            'take_from',
            'destination',
            'parent',
            'sales_order',
            'link',
        ]


class BuildOutputDeleteForm(HelperForm):
    """
    Form for deleting a build output.
    """

    confirm = forms.BooleanField(
        required=False,
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


class UnallocateBuildForm(HelperForm):
    """
    Form for auto-de-allocation of stock from a build
    """

    confirm = forms.BooleanField(required=False, help_text=_('Confirm unallocation of stock'))

    output_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )

    part_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Build
        fields = [
            'confirm',
            'output_id',
            'part_id',
        ]


class AutoAllocateForm(HelperForm):
    """ Form for auto-allocation of stock to a build """

    confirm = forms.BooleanField(required=False, help_text=_('Confirm'))

    output_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Build
        fields = [
            'confirm',
            'output_id',
        ]


class CompleteBuildForm(HelperForm):
    """ Form for marking a Build as complete """

    field_prefix = {
        'serial_numbers': 'fa-hashtag',
    }

    field_placeholder = {
    }

    location = forms.ModelChoiceField(
        queryset=StockLocation.objects.all(),
        help_text=_('Location of completed parts'),
    )

    serial_numbers = forms.CharField(
        label=_('Serial numbers'),
        required=False,
        help_text=_('Enter unique serial numbers (or leave blank)')
    )

    confirm = forms.BooleanField(required=False, help_text=_('Confirm build completion'))

    class Meta:
        model = Build
        fields = [
            'serial_numbers',
            'location',
            'confirm'
        ]


class CancelBuildForm(HelperForm):
    """ Form for cancelling a build """

    confirm_cancel = forms.BooleanField(required=False, help_text=_('Confirm build cancellation'))

    class Meta:
        model = Build
        fields = [
            'confirm_cancel'
        ]


class EditBuildItemForm(HelperForm):
    """
    Form for creating (or editing) a BuildItem object.
    """

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5, help_text=_('Select quantity of stock to allocate'))

    class Meta:
        model = BuildItem
        fields = [
            'build',
            'stock_item',
            'quantity',
            'install_into',
        ]


class EditBuildAttachmentForm(HelperForm):
    """
    Form for creating / editing a BuildAttachment object
    """

    class Meta:
        model = BuildOrderAttachment
        fields = [
            'build',
            'attachment',
            'comment'
        ]
