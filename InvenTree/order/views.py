"""
Django views for interacting with Order app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import DetailView, ListView

from .models import PurchaseOrder

from InvenTree.status_codes import OrderStatus


class PurchaseOrderIndex(ListView):

    model = PurchaseOrder
    template_name = 'order/purchase_orders.html'
    context_object_name = 'orders'

    def get_context_data(self):
        ctx = super().get_context_data()

        ctx['OrderStatus'] = OrderStatus

        return ctx
