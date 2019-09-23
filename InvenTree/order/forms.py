"""
Django Forms for interacting with Order objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext as _

from mptt.fields import TreeNodeChoiceField

from InvenTree.forms import HelperForm

from stock.models import StockLocation
from .models import PurchaseOrder, PurchaseOrderLineItem


class IssuePurchaseOrderForm(HelperForm):

    confirm = forms.BooleanField(required=False, help_text=_('Place order'))

    class Meta:
        model = PurchaseOrder
        fields = [
            'confirm',
        ]


class CancelPurchaseOrderForm(HelperForm):

    confirm = forms.BooleanField(required=False, help_text=_('Cancel order'))

    class Meta:
        model = PurchaseOrder
        fields = [
            'confirm',
        ]
        

class ReceivePurchaseOrderForm(HelperForm):

    location = TreeNodeChoiceField(queryset=StockLocation.objects.all(), required=True, help_text=_('Receive parts to this location'))

    class Meta:
        model = PurchaseOrder
        fields = [
            'location',
        ]


class EditPurchaseOrderForm(HelperForm):
    """ Form for editing a PurchaseOrder object """

    class Meta:
        model = PurchaseOrder
        fields = [
            'reference',
            'supplier',
            'description',
            'URL',
            'notes'
        ]


class EditPurchaseOrderLineItemForm(HelperForm):
    """ Form for editing a PurchaseOrderLineItem object """

    class Meta:
        model = PurchaseOrderLineItem
        fields = [
            'order',
            'part',
            'quantity',
            'reference',
            'notes',
        ]
