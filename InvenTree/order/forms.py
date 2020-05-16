"""
Django Forms for interacting with Order objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext as _

from mptt.fields import TreeNodeChoiceField

from InvenTree.forms import HelperForm
from InvenTree.fields import RoundingDecimalFormField

from stock.models import StockLocation
from .models import PurchaseOrder, PurchaseOrderLineItem, PurchaseOrderAttachment
from .models import SalesOrder, SalesOrderLineItem, SalesOrderAttachment
from .models import SalesOrderAllocation


class IssuePurchaseOrderForm(HelperForm):

    confirm = forms.BooleanField(required=False, help_text=_('Place order'))

    class Meta:
        model = PurchaseOrder
        fields = [
            'confirm',
        ]


class CompletePurchaseOrderForm(HelperForm):

    confirm = forms.BooleanField(required=False, help_text=_("Mark order as complete"))

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


class CancelSalesOrderForm(HelperForm):

    confirm = forms.BooleanField(required=False, help_text=_('Cancel order'))

    class Meta:
        model = SalesOrder
        fields = [
            'confirm',
        ]
        

class ShipSalesOrderForm(HelperForm):

    confirm = forms.BooleanField(required=False, help_text=_('Ship order'))

    class Meta:
        model = SalesOrder
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

    def __init__(self, *args, **kwargs):

        self.field_prefix = {
            'reference': 'PO',
            'link': 'fa-link',
        }

        self.field_placeholder = {
            'reference': _('Enter purchase order number'),
        }

        super().__init__(*args, **kwargs)

    class Meta:
        model = PurchaseOrder
        fields = [
            'reference',
            'supplier',
            'supplier_reference',
            'description',
            'link',
        ]


class EditSalesOrderForm(HelperForm):
    """ Form for editing a SalesOrder object """

    def __init__(self, *args, **kwargs):

        self.field_prefix = {
            'reference': 'SO',
            'link': 'fa-link',
        }

        self.field_placeholder = {
            'reference': _('Enter sales order number'),
        }

        super().__init__(*args, **kwargs)

    class Meta:
        model = SalesOrder
        fields = [
            'reference',
            'customer',
            'customer_reference',
            'description',
            'link'
        ]


class EditPurchaseOrderAttachmentForm(HelperForm):
    """ Form for editing a PurchaseOrderAttachment object """

    class Meta:
        model = PurchaseOrderAttachment
        fields = [
            'order',
            'attachment',
            'comment'
        ]


class EditSalesOrderAttachmentForm(HelperForm):
    """ Form for editing a SalesOrderAttachment object """

    class Meta:
        model = SalesOrderAttachment
        fields = [
            'order',
            'attachment',
            'comment'
        ]


class EditPurchaseOrderLineItemForm(HelperForm):
    """ Form for editing a PurchaseOrderLineItem object """

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5)

    class Meta:
        model = PurchaseOrderLineItem
        fields = [
            'order',
            'part',
            'quantity',
            'reference',
            'notes',
        ]


class EditSalesOrderLineItemForm(HelperForm):
    """ Form for editing a SalesOrderLineItem object """

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5)

    class Meta:
        model = SalesOrderLineItem
        fields = [
            'order',
            'part',
            'quantity',
            'reference',
            'notes'
        ]


class EditSalesOrderAllocationForm(HelperForm):

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5)

    class Meta:
        model = SalesOrderAllocation

        fields = [
            'line',
            'item',
            'quantity']
