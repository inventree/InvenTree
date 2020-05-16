"""
Django Forms for interacting with Build objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from InvenTree.forms import HelperForm
from django import forms
from .models import Build, BuildItem
from stock.models import StockLocation


class EditBuildForm(HelperForm):
    """ Form for editing a Build object.
    """

    class Meta:
        model = Build
        fields = [
            'title',
            'part',
            'parent',
            'sales_order',
            'quantity',
            'take_from',
            'batch',
            'link',
        ]


class ConfirmBuildForm(HelperForm):
    """ Form for auto-allocation of stock to a build """

    confirm = forms.BooleanField(required=False, help_text=_('Confirm'))

    class Meta:
        model = Build
        fields = [
            'confirm'
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

    confirm_cancel = forms.BooleanField(required=False, help_text='Confirm build cancellation')

    class Meta:
        model = Build
        fields = [
            'confirm_cancel'
        ]


class EditBuildItemForm(HelperForm):
    """ Form for adding a new BuildItem to a Build """

    class Meta:
        model = BuildItem
        fields = [
            'build',
            'stock_item',
            'quantity',
        ]
