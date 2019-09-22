"""
Django Forms for interacting with Order objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext as _

from InvenTree.forms import HelperForm

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
