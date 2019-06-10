"""
Django views for interacting with Order app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from django.views.generic import DetailView, ListView
from django.forms import HiddenInput

from .models import PurchaseOrder, PurchaseOrderLineItem
from company.models import Company, SupplierPart

from . import forms as order_forms

from InvenTree.views import AjaxCreateView, AjaxUpdateView
from InvenTree.helpers import str2bool

from InvenTree.status_codes import OrderStatus


class PurchaseOrderIndex(ListView):
    """ List view for all purchase orders """

    model = PurchaseOrder
    template_name = 'order/purchase_orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        """ Retrieve the list of purchase orders,
        ensure that the most recent ones are returned first. """

        queryset = PurchaseOrder.objects.all().order_by('-creation_date')

        return queryset

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


class PurchaseOrderCreate(AjaxCreateView):
    """ View for creating a new PurchaseOrder object using a modal form """

    model = PurchaseOrder
    ajax_form_title = "Create Purchase Order"
    form_class = order_forms.EditPurchaseOrderForm

    def get_initial(self):
        initials = super().get_initial().copy()

        initials['status'] = OrderStatus.PENDING

        supplier_id = self.request.GET.get('supplier', None)

        if supplier_id:
            try:
                supplier = Company.objects.get(id=supplier_id)
                initials['supplier'] = supplier
            except Company.DoesNotExist:
                pass

        return initials


class PurchaseOrderEdit(AjaxUpdateView):
    """ View for editing a PurchaseOrder using a modal form """

    model = PurchaseOrder
    ajax_form_title = 'Edit Purchase Order'
    form_class = order_forms.EditPurchaseOrderForm

    def get_form(self):

        form = super(AjaxUpdateView, self).get_form()

        order = self.get_object()

        # Prevent user from editing supplier if there are already lines in the order
        if order.lines.count() > 0 or not order.status == OrderStatus.PENDING:
            form.fields['supplier'].widget = HiddenInput()

        return form


class PurchaseOrderIssue(AjaxUpdateView):
    """ View for changing a purchase order from 'PENDING' to 'ISSUED' """

    model = PurchaseOrder
    ajax_form_title = 'Issue Order'
    ajax_template_name = "order/order_issue.html"
    form_class = order_forms.IssuePurchaseOrderForm

    def post(self, request, *args, **kwargs):
        """ Mark the purchase order as 'PLACED' """

        order = self.get_object()
        form = self.get_form()

        confirm = str2bool(request.POST.get('confirm', False))

        valid = False

        if not confirm:
            form.errors['confirm'] = [_('Confirm order placement')]
        else:
            valid = True

        data = {
            'form_valid': valid,
        }

        if valid:
            order.place_order()

        return self.renderJsonResponse(request, form, data)


class POLineItemCreate(AjaxCreateView):
    """ AJAX view for creating a new PurchaseOrderLineItem object
    """

    model = PurchaseOrderLineItem
    context_object_name = 'line'
    form_class = order_forms.EditPurchaseOrderLineItemForm
    ajax_form_title = 'Add Line Item'

    def post(self, request, *arg, **kwargs):

        self.request = request

        form = self.get_form()

        valid = form.is_valid()

        part_id = form['part'].value()

        try:
            SupplierPart.objects.get(id=part_id)
        except (SupplierPart.DoesNotExist, ValueError):
            valid = False
            form.errors['part'] = [_('This field is required')]

        data = {
            'form_valid': valid,
        }

        if valid:
            self.object = form.save()

            data['pk'] = self.object.pk
            data['text'] = str(self.object)
        else:
            self.object = None
        
        return self.renderJsonResponse(request, form, data,)

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

            exclude = []

            for line in order.lines.all():
                if line.part and line.part.id not in exclude:
                    exclude.append(line.part.id)

            # Remove parts that are already in the order
            query = query.exclude(id__in=exclude)

            form.fields['part'].queryset = query
            form.fields['order'].widget = HiddenInput()
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
    form_class = order_forms.EditPurchaseOrderLineItemForm
    ajax_template_name = 'modal_form.html'
    ajax_form_action = 'Edit Line Item'
