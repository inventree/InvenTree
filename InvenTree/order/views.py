"""
Django views for interacting with Order app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, ListView
from django.forms import HiddenInput

import logging

from .models import PurchaseOrder, PurchaseOrderLineItem
from build.models import Build
from company.models import Company, SupplierPart
from stock.models import StockItem, StockLocation
from part.models import Part

from . import forms as order_forms

from InvenTree.views import AjaxView, AjaxCreateView, AjaxUpdateView, AjaxDeleteView
from InvenTree.helpers import DownloadFile, str2bool

from InvenTree.status_codes import OrderStatus

logger = logging.getLogger(__name__)


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


class PurchaseOrderExport(AjaxView):
    """ File download for a purchase order

    - File format can be optionally passed as a query param e.g. ?format=CSV
    - Default file format is CSV
    """

    model = PurchaseOrder

    def get(self, request, *args, **kwargs):

        order = get_object_or_404(PurchaseOrder, pk=self.kwargs['pk'])

        export_format = request.GET.get('format', 'csv')

        filename = '{order} - {company}.{fmt}'.format(
            order=str(order),
            company=order.supplier.name,
            fmt=export_format
        )

        filedata = order.export_to_file(format=export_format)

        return DownloadFile(filedata, filename)


class PurchaseOrderReceive(AjaxView):
    """ View for receiving parts which are outstanding against a PurchaseOrder.

    Any parts which are outstanding are listed.
    If all parts are marked as received, the order is closed out.

    """

    ajax_form_title = "Receive Parts"
    ajax_template_name = "order/receive_parts.html"

    # Where the parts will be going (selected in POST request)
    destination = None

    def get_context_data(self):

        ctx = {
            'order': self.order,
            'lines': self.lines,
            'locations': StockLocation.objects.all(),
            'destination': self.destination,
        }

        return ctx

    def get(self, request, *args, **kwargs):
        """ Respond to a GET request. Determines which parts are outstanding,
        and presents a list of these parts to the user.
        """

        self.request = request
        self.order = get_object_or_404(PurchaseOrder, pk=self.kwargs['pk'])

        self.lines = self.order.pending_line_items()

        for line in self.lines:
            # Pre-fill the remaining quantity
            line.receive_quantity = line.remaining()

        return self.renderJsonResponse(request)

    def post(self, request, *args, **kwargs):
        """ Respond to a POST request. Data checking and error handling.
        If the request is valid, new StockItem objects will be made
        for each received item.
        """

        self.request = request
        self.order = get_object_or_404(PurchaseOrder, pk=self.kwargs['pk'])

        self.lines = []
        self.destination = None

        # Extract the destination for received parts
        if 'receive_location' in request.POST:
            pk = request.POST['receive_location']
            try:
                self.destination = StockLocation.objects.get(id=pk)
            except (StockLocation.DoesNotExist, ValueError):
                pass

        errors = self.destination is None

        # Extract information on all submitted line items
        for item in request.POST:
            if item.startswith('line-'):
                pk = item.replace('line-', '')

                try:
                    line = PurchaseOrderLineItem.objects.get(id=pk)
                except (PurchaseOrderLineItem.DoesNotExist, ValueError):
                    continue

                # Ignore a part that doesn't map to a SupplierPart
                try:
                    if line.part is None:
                        continue
                except SupplierPart.DoesNotExist:
                    continue

                receive = self.request.POST[item]

                try:
                    receive = int(receive)
                except ValueError:
                    # In the case on an invalid input, reset to default
                    receive = line.remaining()
                    errors = True

                if receive < 0:
                    receive = 0
                    errors = True

                line.receive_quantity = receive
                self.lines.append(line)

        # No errors? Receive the submitted parts!
        if errors is False:
            self.receive_parts()

        data = {
            'form_valid': errors is False,
            'success': 'Items marked as received',
        }

        return self.renderJsonResponse(request, data=data)

    def receive_parts(self):
        """ Called once the form has been validated.
        Create new stockitems against received parts.
        """

        for line in self.lines:

            if not line.part:
                continue

            self.order.receive_line_item(line, self.destination, line.receive_quantity, self.request.user)


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

        for supplier in self.suppliers:
            supplier.order_items = []
            suppliers[supplier.name] = supplier

        for part in self.parts:
            supplier_part_id = part.order_supplier

            try:
                supplier = SupplierPart.objects.get(pk=supplier_part_id).supplier
            except SupplierPart.DoesNotExist:
                continue

            if supplier.name not in suppliers:
                supplier.order_items = []
                supplier.selected_purchase_order = None
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
                    # If ordering from a Build page, ignore parts that we have enough of
                    if part.quantity_to_order <= 0:
                        continue
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
        """ Handle the POST action for part selection.

        - Validates each part / quantity / supplier / etc

        Part selection form contains the following fields for each part:

        - supplier-<pk> : The ID of the selected supplier
        - quantity-<pk> : The quantity to add to the order
        """

        self.request = request

        self.parts = []
        self.suppliers = []

        # Any errors for the part selection form?
        part_errors = False
        supplier_errors = False

        # Extract part information from the form
        for item in self.request.POST:
            
            if item.startswith('part-supplier-'):
                
                pk = item.replace('part-supplier-', '')
                
                # Check that the part actually exists
                try:
                    part = Part.objects.get(id=pk)
                except (Part.DoesNotExist, ValueError):
                    continue
                
                supplier_part_id = self.request.POST[item]
                
                quantity = self.request.POST.get('part-quantity-' + str(pk), 0)

                # Ensure a valid supplier has been passed
                try:
                    supplier_part = SupplierPart.objects.get(id=supplier_part_id)
                except (SupplierPart.DoesNotExist, ValueError):
                    supplier_part = None

                # Ensure a valid quantity is passed
                try:
                    quantity = int(quantity)

                    # Eliminate lines where the quantity is zero
                    if quantity == 0:
                        continue
                except ValueError:
                    quantity = part.quantity_to_order

                part.order_supplier = supplier_part.id if supplier_part else None
                part.order_quantity = quantity

                self.parts.append(part)

                if supplier_part is None:
                    part_errors = True

                elif quantity < 0:
                    part_errors = True

            elif item.startswith('purchase-order-'):
                # Which purchase order is selected for a given supplier?
                pk = item.replace('purchase-order-', '')

                # Check that the Supplier actually exists
                try:
                    supplier = Company.objects.get(id=pk)
                except Company.DoesNotExist:
                    # Skip this item
                    continue

                purchase_order_id = self.request.POST[item]

                # Ensure that a valid purchase order has been passed
                try:
                    purchase_order = PurchaseOrder.objects.get(pk=purchase_order_id)
                except (PurchaseOrder.DoesNotExist, ValueError):
                    purchase_order = None

                supplier.selected_purchase_order = purchase_order.id if purchase_order else None

                self.suppliers.append(supplier)

                if supplier.selected_purchase_order is None:
                    supplier_errors = True

        form_step = request.POST.get('form_step')

        # Map parts to suppliers
        self.get_suppliers()

        valid = False

        if form_step == 'select_parts':
            # No errors? Proceed to PO selection form
            if part_errors is False:
                self.ajax_template_name = 'order/order_wizard/select_pos.html'

            else:
                self.ajax_template_name = 'order/order_wizard/select_parts.html'

        elif form_step == 'select_purchase_orders':

            self.ajax_template_name = 'order/order_wizard/select_pos.html'

            valid = part_errors is False and supplier_errors is False

            # Form wizard is complete! Add items to purchase orders
            if valid:
                self.order_items()

        data = {
            'form_valid': valid,
            'success': 'Ordered {n} parts'.format(n=len(self.parts))
        }

        return self.renderJsonResponse(self.request, data=data)

    def order_items(self):
        """ Add the selected items to the purchase orders. """

        for supplier in self.suppliers:

            # Check that the purchase order does actually exist
            try:
                order = PurchaseOrder.objects.get(pk=supplier.selected_purchase_order)
            except PurchaseOrder.DoesNotExist:
                logger.critical('Could not add items to purchase order {po} - Order does not exist'.format(po=supplier.selected_purchase_order))
                continue

            for item in supplier.order_items:

                # Ensure that the quantity is valid
                try:
                    quantity = int(item.order_quantity)
                    if quantity <= 0:
                        continue
                except ValueError:
                    logger.warning("Did not add part to purchase order - incorrect quantity")
                    continue

                # Check that the supplier part does actually exist
                try:
                    supplier_part = SupplierPart.objects.get(pk=item.order_supplier)
                except SupplierPart.DoesNotExist:
                    logger.critical("Could not add part '{part}' to purchase order - selected supplier part '{sp}' does not exist.".format(
                        part=item,
                        sp=item.order_supplier))
                    continue

                order.add_line_item(supplier_part, quantity)


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
    """ View for editing a PurchaseOrderLineItem object in a modal form.
    """

    model = PurchaseOrderLineItem
    form_class = order_forms.EditPurchaseOrderLineItemForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Line Item'

    def get_form(self):
        form = super().get_form()

        # Prevent user from editing order once line item is assigned
        form.fields.pop('order')

        return form


class POLineItemDelete(AjaxDeleteView):
    """ View for deleting a PurchaseOrderLineItem object in a modal form
    """

    model = PurchaseOrderLineItem
    ajax_form_title = 'Delete Line Item'
    ajax_template_name = 'order/po_lineitem_delete.html'
    
    def get_data(self):
        return {
            'danger': 'Deleted line item',
        }
