"""
Django views for interacting with Order app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from django.views.generic import DetailView, ListView
from django.forms import HiddenInput

from .models import PurchaseOrder, PurchaseOrderLineItem
from build.models import Build
from company.models import Company, SupplierPart
from stock.models import StockItem
from part.models import Part

from . import forms as order_forms

from InvenTree.views import AjaxView, AjaxCreateView, AjaxUpdateView
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


class OrderParts(AjaxView):
    """ View for adding various SupplierPart items to a Purchase Order.

    SupplierParts can be selected from a variety of 'sources':

    - ?supplier_parts[]= -> Direct list of SupplierPart objects
    - ?parts[]= -> List of base Part objects (user must then select supplier parts)
    - ?stock[]= -> List of StockItem objects (user must select supplier parts)
    - ?build= -> A Build object (user must select parts, then supplier parts)

    """

    ajax_form_title = "Order Parts"
    ajax_template_name = 'order/order_wizard/select_parts.html'

    # List of Parts we wish to order
    parts = []
    suppliers = []

    def get_context_data(self):

        ctx = {}

        ctx['parts'] = sorted(self.parts, key=lambda part: int(part.order_quantity), reverse=True)
        ctx['suppliers'] = self.suppliers

        return ctx

    def get_suppliers(self):
        """ Calculates a list of suppliers which the user will need to create POs for.
        This is calculated AFTER the user finishes selecting the parts to order.
        Crucially, get_parts() must be called before get_suppliers()
        """

        suppliers = {}

        for part in self.parts:
            supplier_part_id = part.order_supplier

            try:
                supplier = SupplierPart.objects.get(pk=supplier_part_id).supplier
            except SupplierPart.DoesNotExist:
                continue

            if not supplier.name in suppliers:
                supplier.order_items = []
                suppliers[supplier.name] = supplier
                
            suppliers[supplier.name].order_items.append(part)

        self.suppliers = [suppliers[key] for key in suppliers.keys()]

    def get_parts(self):
        """ Determine which parts the user wishes to order.
        This is performed on the initial GET request.
        """

        self.parts = []

        part_ids = set()

        # User has passed a list of stock items
        if 'stock[]' in self.request.GET:

            stock_id_list = self.request.GET.getlist('stock[]')
            
            """ Get a list of all the parts associated with the stock items.
            - Base part must be purchaseable.
            - Return a set of corresponding Part IDs
            """
            stock_items = StockItem.objects.filter(
                part__purchaseable=True,
                id__in=stock_id_list)

            for item in stock_items:
                part_ids.add(item.part.id)

        # User has passed a single Part ID
        elif 'part' in self.request.GET:
            try:
                part_id = self.request.GET.get('part')
                part = Part.objects.get(id=part_id)

                part_ids.add(part.id)

            except Part.DoesNotExist:
                pass

        # User has passed a list of part ID values
        elif 'parts[]' in self.request.GET:
            part_id_list = self.request.GET.getlist('parts[]')

            parts = Part.objects.filter(
                purchaseable=True,
                id__in=part_id_list)

            for part in parts:
                part_ids.add(part.id)

        # User has provided a Build ID
        elif 'build' in self.request.GET:
            build_id = self.request.GET.get('build')
            try:
                build = Build.objects.get(id=build_id)

                parts = build.part.required_parts()

                for part in parts:
                    part_ids.add(part.id)
            except Build.DoesNotExist:
                pass

        # Create the list of parts
        for id in part_ids:
            try:
                part = Part.objects.get(id=id)
                # Pre-fill the 'order quantity' value
                part.order_quantity = part.quantity_to_order

                default_supplier = part.get_default_supplier()

                if default_supplier:
                    part.order_supplier = default_supplier.id
                else:
                    part.order_supplier = None
            except Part.DoesNotExist:
                continue

            self.parts.append(part)

    def get(self, request, *args, **kwargs):

        self.request = request

        self.get_parts()

        return self.renderJsonResponse(request)

    def post(self, request, *args, **kwargs):

        self.request = request
        form_step = request.POST.get('form_step')

        if form_step == 'select_parts':
            return self.handlePartSelection()
        elif form_step == 'assign_orders':
            return self.handleOrderAssignment()
        
        data = {
            'form_valid': False,
        }

        return self.renderJsonResponse(request, data=data)

    def handlePartSelection(self):
        """ Handle the POST action for part selection.

        - Validates each part / quantity / supplier / etc

        Part selection form contains the following fields for each part:

        - supplier-<pk> : The ID of the selected supplier
        - quantity-<pk> : The quantity to add to the order
        """

        self.parts = []

        # Any errors for the part selection form?
        errors = False

        for item in self.request.POST:
            
            if item.startswith('supplier-'):
                
                pk = item.replace('supplier-', '')
                
                # Check that the part actually exists
                try:
                    part = Part.objects.get(id=pk)
                except (Part.DoesNotExist, ValueError):
                    continue
                
                supplier_part_id = self.request.POST[item]
                
                quantity = self.request.POST.get('quantity-' + str(pk), 0)

                # Ensure a valid supplier has been passed
                try:
                    supplier_part = SupplierPart.objects.get(id=supplier_part_id)
                except (SupplierPart.DoesNotExist, ValueError):
                    supplier_part = None
                    print('Error getting supplier part for ID', supplier_part_id)

                # Ensure a valid quantity is passed
                try:
                    q = int(quantity)
                    # Ignore any parts for which the selected quantity is zero
                    if q <= 0:
                        continue
                except ValueError:
                    quantity = part.quantity_to_order

                part.order_supplier = supplier_part.id if supplier_part else None
                part.order_quantity = quantity

                self.parts.append(part)

                if supplier_part is None:
                    errors = True

        data = {
            'form_valid': False,
        }

        # No errors? Proceed to PO selection form
        if errors == False:
            self.ajax_template_name = 'order/order_wizard/select_pos.html'
            self.get_suppliers()

        return self.renderJsonResponse(self.request, data=data)


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
