"""
Django views for interacting with Order app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import DetailView, ListView

from .models import PurchaseOrder, PurchaseOrderLineItem
from .forms import EditPurchaseOrderLineItemForm

from InvenTree.views import AjaxCreateView, AjaxUpdateView, AjaxDeleteView

from InvenTree.status_codes import OrderStatus


class PurchaseOrderIndex(ListView):
    """ List view for all purchase orders """

    model = PurchaseOrder
    template_name = 'order/purchase_orders.html'
    context_object_name = 'orders'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx['OrderStatus'] = OrderStatus

        return ctx


class PurchaseOrderDetail(DetailView):
    """ Detail view for a PurchaseOrder object """

    context_object_name = 'order'
    queryset = PurchaseOrder.objects.all().prefetch_related('lines')
    template_name = 'order/purchase_order_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx['OrderStatus'] = OrderStatus

        return ctx


class POLineItemCreate(AjaxCreateView):
    """ AJAX view for creating a new PurchaseOrderLineItem object
    """

    model = PurchaseOrderLineItem
    context_object_name = 'line'
    form_class = EditPurchaseOrderLineItemForm
    ajax_template_name = 'modal_form.html'
    ajax_form_action = 'Add Line Item'

    def get_form(self):
        """ Limit choice options based on the selected order, etc
        """

        form = super().get_form()

        order_id = form['order'].value()

        try:
            order = PurchaseOrder.objects.get(id=order_id)

            query = form.fields['part'].queryset

            # Only allow parts from the selected supplier
            query = query.filter(supplier=order.supplier.id)

            # Remove parts that are already in the order
            query = query.exclude(id__in=[line.part.id for line in order.lines.all()])

            form.fields['part'].queryset = query
        except PurchaseOrder.DoesNotExist:
            pass

        return form


    def get_initial(self):
        """ Extract initial data for the line item.

        - The 'order' will be passed as a query parameter
        - Use this to set the 'order' field and limit the options for 'part'
        """

        initials = super().get_initial().copy()

        order_id = self.request.GET.get('order', None)

        if order_id:
            try:
                order = PurchaseOrder.objects.get(id=order_id)
                initials['order'] = order

            except PurchaseOrder.DoesNotExist:
                pass

        return initials


class POLineItemEdit(AjaxUpdateView):

    model = PurchaseOrderLineItem
    form_class = EditPurchaseOrderLineItemForm
    ajax_template_name = 'modal_form.html'
    ajax_form_action = 'Edit Line Item'
