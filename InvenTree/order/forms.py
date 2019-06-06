"""
Django Forms for interacting with Order objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm

from .models import PurchaseOrder, PurchaseOrderLineItem


class IssuePurchaseOrderForm(HelperForm):

    class Meta:
        model = PurchaseOrder
        fields = [
            'status',
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
            'received'
        ]
