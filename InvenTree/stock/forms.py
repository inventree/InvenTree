"""
Django Forms for interacting with Stock app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.forms.utils import ErrorDict
from django.utils.translation import gettext_lazy as _

from mptt.fields import TreeNodeChoiceField

from InvenTree.forms import HelperForm
from InvenTree.fields import RoundingDecimalFormField
from InvenTree.fields import DatePickerFormField

from .models import StockLocation, StockItem, StockItemTracking


class ReturnStockItemForm(HelperForm):
    """
    Form for manually returning a StockItem into stock

    TODO: This could be a simple API driven form!
    """

    class Meta:
        model = StockItem
        fields = [
            'location',
        ]


class ConvertStockItemForm(HelperForm):
    """
    Form for converting a StockItem to a variant of its current part.

    TODO: Migrate this form to the modern API forms interface
    """

    class Meta:
        model = StockItem
        fields = [
            'part'
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
