"""
Django Forms for interacting with Build objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
            'quantity',
            'batch',
            'URL',
            'notes',
        ]


class AutoAllocateBuildForm(HelperForm):
    """ Form for auto-allocation of stock to a build """

    confirm = forms.BooleanField(required=False, help_text='Confirm stock allocation')

    class Meta:
        model = Build
        fields = [
            'confirm'
        ]


class CompleteBuildForm(HelperForm):
    """ Form for marking a Build as complete """

    location = forms.ModelChoiceField(
        queryset=StockLocation.objects.all(),
        help_text='Location of completed parts',
    )

    confirm = forms.BooleanField(required=False, help_text='Confirm build submission')

    class Meta:
        model = Build
        fields = [
            'location',
            'confirm'
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
