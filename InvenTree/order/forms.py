"""
Django Forms for interacting with Order objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from mptt.fields import TreeNodeChoiceField

from InvenTree.forms import HelperForm
from InvenTree.fields import InvenTreeMoneyField, RoundingDecimalFormField

from InvenTree.helpers import clean_decimal

from common.forms import MatchItemForm

import part.models

from stock.models import StockLocation
from .models import PurchaseOrder
from .models import SalesOrder, SalesOrderLineItem
from .models import SalesOrderAllocation


class IssuePurchaseOrderForm(HelperForm):

    confirm = forms.BooleanField(required=True, initial=False, label=_('Confirm'), help_text=_('Place order'))

    class Meta:
        model = PurchaseOrder
        fields = [
            'confirm',
        ]


class CompletePurchaseOrderForm(HelperForm):

    confirm = forms.BooleanField(required=True, label=_('Confirm'), help_text=_("Mark order as complete"))

    class Meta:
        model = PurchaseOrder
        fields = [
            'confirm',
        ]


class CancelPurchaseOrderForm(HelperForm):

    confirm = forms.BooleanField(required=True, label=_('Confirm'), help_text=_('Cancel order'))

    class Meta:
        model = PurchaseOrder
        fields = [
            'confirm',
        ]


class CancelSalesOrderForm(HelperForm):

    confirm = forms.BooleanField(required=True, label=_('Confirm'), help_text=_('Cancel order'))

    class Meta:
        model = SalesOrder
        fields = [
            'confirm',
        ]


class ShipSalesOrderForm(HelperForm):

    confirm = forms.BooleanField(required=True, label=_('Confirm'), help_text=_('Ship order'))

    class Meta:
        model = SalesOrder
        fields = [
            'confirm',
        ]


class AllocateSerialsToSalesOrderForm(forms.Form):
    """
    Form for assigning stock to a sales order,
    by serial number lookup
    """

    line = forms.ModelChoiceField(
        queryset=SalesOrderLineItem.objects.all(),
    )

    part = forms.ModelChoiceField(
        queryset=part.models.Part.objects.all(),
    )

    serials = forms.CharField(
        label=_("Serial Numbers"),
        required=True,
        help_text=_('Enter stock item serial numbers'),
    )

    quantity = forms.IntegerField(
        label=_('Quantity'),
        required=True,
        help_text=_('Enter quantity of stock items'),
        initial=1,
        min_value=1
    )

    class Meta:

        fields = [
            'line',
            'part',
            'serials',
            'quantity',
        ]


class CreateSalesOrderAllocationForm(HelperForm):
    """
    Form for creating a SalesOrderAllocation item.
    """

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5, label=_('Quantity'))

    class Meta:
        model = SalesOrderAllocation

        fields = [
            'line',
            'item',
            'quantity',
        ]


class EditSalesOrderAllocationForm(HelperForm):
    """
    Form for editing a SalesOrderAllocation item
    """

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5, label=_('Quantity'))

    class Meta:
        model = SalesOrderAllocation

        fields = [
            'line',
            'item',
            'quantity']


class OrderMatchItemForm(MatchItemForm):
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
        # set price field
        elif 'price' in col_guess.lower():
            return InvenTreeMoneyField(
                label=_(col_guess),
                decimal_places=5,
                max_digits=19,
                required=False,
                default_amount=clean_decimal(row.get('purchase_price', '')),
            )

        # return default
        return super().get_special_field(col_guess, row, file_manager)
