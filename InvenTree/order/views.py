"""
Django views for interacting with Order app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, ListView, UpdateView
from django.forms import HiddenInput

import logging
from decimal import Decimal, InvalidOperation

from .models import PurchaseOrder, PurchaseOrderLineItem, PurchaseOrderAttachment
from .models import SalesOrder, SalesOrderLineItem, SalesOrderAttachment
from .models import SalesOrderAllocation
from .admin import POLineItemResource
from build.models import Build
from company.models import Company, SupplierPart
from stock.models import StockItem, StockLocation
from part.models import Part

from common.models import InvenTreeSetting

from . import forms as order_forms

from InvenTree.views import AjaxView, AjaxCreateView, AjaxUpdateView, AjaxDeleteView
from InvenTree.helpers import DownloadFile, str2bool
from InvenTree.views import InvenTreeRoleMixin

from InvenTree.status_codes import PurchaseOrderStatus, SalesOrderStatus, StockStatus

logger = logging.getLogger(__name__)


class PurchaseOrderIndex(InvenTreeRoleMixin, ListView):
    """ List view for all purchase orders """

    model = PurchaseOrder
    template_name = 'order/purchase_orders.html'
    context_object_name = 'orders'

    role_required = 'purchase_order.view'

    def get_queryset(self):
        """ Retrieve the list of purchase orders,
        ensure that the most recent ones are returned first. """

        queryset = PurchaseOrder.objects.all().order_by('-creation_date')

        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        return ctx


class SalesOrderIndex(InvenTreeRoleMixin, ListView):

    model = SalesOrder
    template_name = 'order/sales_orders.html'
    context_object_name = 'orders'
    role_required = 'sales_order.view'


class PurchaseOrderDetail(InvenTreeRoleMixin, DetailView):
    """ Detail view for a PurchaseOrder object """

    context_object_name = 'order'
    queryset = PurchaseOrder.objects.all().prefetch_related('lines')
    template_name = 'order/purchase_order_detail.html'
    role_required = 'purchase_order.view'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        return ctx


class SalesOrderDetail(InvenTreeRoleMixin, DetailView):
    """ Detail view for a SalesOrder object """

    context_object_name = 'order'
    queryset = SalesOrder.objects.all().prefetch_related('lines')
    template_name = 'order/sales_order_detail.html'
    role_required = 'sales_order.view'


class PurchaseOrderAttachmentCreate(AjaxCreateView):
    """
    View for creating a new PurchaseOrderAttachment
    """

    model = PurchaseOrderAttachment
    form_class = order_forms.EditPurchaseOrderAttachmentForm
    ajax_form_title = _("Add Purchase Order Attachment")
    ajax_template_name = "modal_form.html"
    role_required = 'purchase_order.add'

    def save(self, form, **kwargs):

        attachment = form.save(commit=False)
        attachment.user = self.request.user
        attachment.save()

    def get_data(self):
        return {
            "success": _("Added attachment")
        }

    def get_initial(self):
        """
        Get initial data for creating a new PurchaseOrderAttachment object.

        - Client must request this form with a parent PurchaseOrder in midn.
        - e.g. ?order=<pk>
        """

        initials = super(AjaxCreateView, self).get_initial()

        try:
            initials["order"] = PurchaseOrder.objects.get(id=self.request.GET.get('order', -1))
        except (ValueError, PurchaseOrder.DoesNotExist):
            pass

        return initials

    def get_form(self):
        """
        Create a form to upload a new PurchaseOrderAttachment

        - Hide the 'order' field
        """

        form = super(AjaxCreateView, self).get_form()

        form.fields['order'].widget = HiddenInput()

        return form


class SalesOrderAttachmentCreate(AjaxCreateView):
    """ View for creating a new SalesOrderAttachment """

    model = SalesOrderAttachment
    form_class = order_forms.EditSalesOrderAttachmentForm
    ajax_form_title = _('Add Sales Order Attachment')
    role_required = 'sales_order.add'

    def save(self, form, **kwargs):
        """
        Save the user that uploaded the attachment
        """
        
        attachment = form.save(commit=False)
        attachment.user = self.request.user
        attachment.save()

    def get_data(self):
        return {
            'success': _('Added attachment')
        }

    def get_initial(self):
        initials = super().get_initial().copy()

        try:
            initials['order'] = SalesOrder.objects.get(id=self.request.GET.get('order', None))
        except (ValueError, SalesOrder.DoesNotExist):
            pass

        return initials

    def get_form(self):
        """ Hide the 'order' field """

        form = super().get_form()
        form.fields['order'].widget = HiddenInput()

        return form


class PurchaseOrderAttachmentEdit(AjaxUpdateView):
    """ View for editing a PurchaseOrderAttachment object """

    model = PurchaseOrderAttachment
    form_class = order_forms.EditPurchaseOrderAttachmentForm
    ajax_form_title = _("Edit Attachment")
    role_required = 'purchase_order.change'

    def get_data(self):
        return {
            'success': _('Attachment updated')
        }

    def get_form(self):
        form = super(AjaxUpdateView, self).get_form()

        # Hide the 'order' field
        form.fields['order'].widget = HiddenInput()

        return form


class SalesOrderAttachmentEdit(AjaxUpdateView):
    """ View for editing a SalesOrderAttachment object """

    model = SalesOrderAttachment
    form_class = order_forms.EditSalesOrderAttachmentForm
    ajax_form_title = _("Edit Attachment")
    role_required = 'sales_order.change'

    def get_data(self):
        return {
            'success': _('Attachment updated')
        }

    def get_form(self):
        form = super().get_form()

        form.fields['order'].widget = HiddenInput()

        return form


class PurchaseOrderAttachmentDelete(AjaxDeleteView):
    """ View for deleting a PurchaseOrderAttachment """

    model = PurchaseOrderAttachment
    ajax_form_title = _("Delete Attachment")
    ajax_template_name = "order/delete_attachment.html"
    context_object_name = "attachment"
    role_required = 'purchase_order.delete'

    def get_data(self):
        return {
            "danger": _("Deleted attachment")
        }


class SalesOrderAttachmentDelete(AjaxDeleteView):
    """ View for deleting a SalesOrderAttachment """

    model = SalesOrderAttachment
    ajax_form_title = _("Delete Attachment")
    ajax_template_name = "order/delete_attachment.html"
    context_object_name = "attachment"
    role_required = 'sales_order.delete'

    def get_data(self):
        return {
            "danger": _("Deleted attachment")
        }


class PurchaseOrderNotes(InvenTreeRoleMixin, UpdateView):
    """ View for updating the 'notes' field of a PurchaseOrder """

    context_object_name = 'order'
    template_name = 'order/order_notes.html'
    model = PurchaseOrder
    role_required = 'purchase_order.view'

    fields = ['notes']

    def get_success_url(self):

        return reverse('po-notes', kwargs={'pk': self.get_object().id})

    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

        ctx['editing'] = str2bool(self.request.GET.get('edit', False))

        return ctx


class SalesOrderNotes(InvenTreeRoleMixin, UpdateView):
    """ View for editing the 'notes' field of a SalesORder """

    context_object_name = 'order'
    template_name = 'order/sales_order_notes.html'
    model = SalesOrder
    role_required = 'sales_order.view'

    fields = ['notes']

    def get_success_url(self):
        return reverse('so-notes', kwargs={'pk': self.get_object().pk})

    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

        ctx['editing'] = str2bool(self.request.GET.get('edit', False))

        return ctx


class PurchaseOrderCreate(AjaxCreateView):
    """
    View for creating a new PurchaseOrder object using a modal form
    """

    model = PurchaseOrder
    ajax_form_title = _("Create Purchase Order")
    form_class = order_forms.EditPurchaseOrderForm
    role_required = 'purchase_order.add'

    def get_initial(self):
        initials = super().get_initial().copy()

        initials['reference'] = PurchaseOrder.getNextOrderNumber()
        initials['status'] = PurchaseOrderStatus.PENDING

        supplier_id = self.request.GET.get('supplier', None)

        if supplier_id:
            try:
                supplier = Company.objects.get(id=supplier_id)
                initials['supplier'] = supplier
            except (Company.DoesNotExist, ValueError):
                pass

        return initials

    def save(self, form, **kwargs):
        """
        Record the user who created this PurchaseOrder
        """

        order = form.save(commit=False)
        order.created_by = self.request.user
        
        return super().save(form)


class SalesOrderCreate(AjaxCreateView):
    """ View for creating a new SalesOrder object """

    model = SalesOrder
    ajax_form_title = _("Create Sales Order")
    form_class = order_forms.EditSalesOrderForm
    role_required = 'sales_order.add'

    def get_initial(self):
        initials = super().get_initial().copy()

        initials['reference'] = SalesOrder.getNextOrderNumber()
        initials['status'] = SalesOrderStatus.PENDING

        customer_id = self.request.GET.get('customer', None)

        if customer_id is not None:
            try:
                customer = Company.objects.get(id=customer_id)
                initials['customer'] = customer
            except (Company.DoesNotExist, ValueError):
                pass

        return initials

    def save(self, form, **kwargs):
        """
        Record the user who created this SalesOrder
        """

        order = form.save(commit=False)
        order.created_by = self.request.user
        
        return super().save(form)


class PurchaseOrderEdit(AjaxUpdateView):
    """ View for editing a PurchaseOrder using a modal form """

    model = PurchaseOrder
    ajax_form_title = _('Edit Purchase Order')
    form_class = order_forms.EditPurchaseOrderForm
    role_required = 'purchase_order.change'

    def get_form(self):

        form = super(AjaxUpdateView, self).get_form()

        order = self.get_object()

        # Prevent user from editing supplier if there are already lines in the order
        if order.lines.count() > 0 or not order.status == PurchaseOrderStatus.PENDING:
            form.fields['supplier'].widget = HiddenInput()

        return form


class SalesOrderEdit(AjaxUpdateView):
    """ View for editing a SalesOrder """

    model = SalesOrder
    ajax_form_title = _('Edit Sales Order')
    form_class = order_forms.EditSalesOrderForm
    role_required = 'sales_order.change'

    def get_form(self):
        form = super().get_form()

        # Prevent user from editing customer
        form.fields['customer'].widget = HiddenInput()

        return form


class PurchaseOrderCancel(AjaxUpdateView):
    """ View for cancelling a purchase order """

    model = PurchaseOrder
    ajax_form_title = _('Cancel Order')
    ajax_template_name = 'order/order_cancel.html'
    form_class = order_forms.CancelPurchaseOrderForm
    role_required = 'purchase_order.change'

    def validate(self, order, form, **kwargs):
        
        confirm = str2bool(form.cleaned_data.get('confirm', False))

        if not confirm:
            form.add_error('confirm', _('Confirm order cancellation'))

        if not order.can_cancel():
            form.add_error(None, _('Order cannot be cancelled as either pending or placed'))

    def save(self, order, form, **kwargs):
        """
        Cancel the PurchaseOrder
        """

        order.cancel_order()


class SalesOrderCancel(AjaxUpdateView):
    """ View for cancelling a sales order """

    model = SalesOrder
    ajax_form_title = _("Cancel sales order")
    ajax_template_name = "order/sales_order_cancel.html"
    form_class = order_forms.CancelSalesOrderForm
    role_required = 'sales_order.change'

    def validate(self, order, form, **kwargs):

        confirm = str2bool(form.cleaned_data.get('confirm', False))

        if not confirm:
            form.add_error('confirm', _('Confirm order cancellation'))

        if not order.can_cancel():
            form.add_error(None, _('Order cannot be cancelled'))

    def save(self, order, form, **kwargs):
        """
        Once the form has been validated, cancel the SalesOrder
        """

        order.cancel_order()


class PurchaseOrderIssue(AjaxUpdateView):
    """ View for changing a purchase order from 'PENDING' to 'ISSUED' """

    model = PurchaseOrder
    ajax_form_title = _('Issue Order')
    ajax_template_name = "order/order_issue.html"
    form_class = order_forms.IssuePurchaseOrderForm
    role_required = 'purchase_order.change'

    def validate(self, order, form, **kwargs):

        confirm = str2bool(self.request.POST.get('confirm', False))

        if not confirm:
            form.add_error('confirm', _('Confirm order placement'))

    def save(self, order, form, **kwargs):
        """
        Once the form has been validated, place the order.
        """
        order.place_order()

    def get_data(self):
        return {
            'success': _('Purchase order issued')
        }


class PurchaseOrderComplete(AjaxUpdateView):
    """ View for marking a PurchaseOrder as complete.
    """

    form_class = order_forms.CompletePurchaseOrderForm
    model = PurchaseOrder
    ajax_template_name = "order/order_complete.html"
    ajax_form_title = _("Complete Order")
    context_object_name = 'order'
    role_required = 'purchase_order.change'

    def get_context_data(self):

        ctx = {
            'order': self.get_object(),
        }

        return ctx

    def validate(self, order, form, **kwargs):

        confirm = str2bool(form.cleaned_data.get('confirm', False))

        if not confirm:
            form.add_error('confirm', _('Confirm order completion'))

    def save(self, order, form, **kwargs):
        """
        Complete the PurchaseOrder
        """

        order.complete_order()

    def get_data(self):
        return {
            'success': _('Purchase order completed')
        }


class SalesOrderShip(AjaxUpdateView):
    """ View for 'shipping' a SalesOrder """
    form_class = order_forms.ShipSalesOrderForm
    model = SalesOrder
    context_object_name = 'order'
    ajax_template_name = 'order/sales_order_ship.html'
    ajax_form_title = _('Ship Order')
    role_required = 'sales_order.change'

    def post(self, request, *args, **kwargs):

        self.request = request

        order = self.get_object()
        self.object = order
        
        form = self.get_form()

        confirm = str2bool(request.POST.get('confirm', False))
        
        valid = False

        if not confirm:
            form.add_error('confirm', _('Confirm order shipment'))
        else:
            valid = True

        if valid:
            if not order.ship_order(request.user):
                form.add_error(None, _('Could not ship order'))
                valid = False

        data = {
            'form_valid': valid,
        }

        context = self.get_context_data()

        context['order'] = order

        return self.renderJsonResponse(request, form, data, context)


class PurchaseOrderExport(AjaxView):
    """ File download for a purchase order

    - File format can be optionally passed as a query param e.g. ?format=CSV
    - Default file format is CSV
    """

    model = PurchaseOrder
    role_required = 'purchase_order.view'

    def get(self, request, *args, **kwargs):

        order = get_object_or_404(PurchaseOrder, pk=self.kwargs['pk'])

        export_format = request.GET.get('format', 'csv')

        filename = '{order} - {company}.{fmt}'.format(
            order=str(order),
            company=order.supplier.name,
            fmt=export_format
        )

        dataset = POLineItemResource().export(queryset=order.lines.all())

        filedata = dataset.export(format=export_format)

        return DownloadFile(filedata, filename)


class PurchaseOrderReceive(AjaxUpdateView):
    """ View for receiving parts which are outstanding against a PurchaseOrder.

    Any parts which are outstanding are listed.
    If all parts are marked as received, the order is closed out.

    """

    form_class = order_forms.ReceivePurchaseOrderForm
    ajax_form_title = _("Receive Parts")
    ajax_template_name = "order/receive_parts.html"
    role_required = 'purchase_order.change'

    # Where the parts will be going (selected in POST request)
    destination = None

    def get_context_data(self):

        ctx = {
            'order': self.order,
            'lines': self.lines,
        }

        return ctx

    def get_lines(self):
        """
        Extract particular line items from the request,
        or default to *all* pending line items if none are provided
        """

        lines = None

        if 'line' in self.request.GET:
            line_id = self.request.GET.get('line')

            try:
                lines = PurchaseOrderLineItem.objects.filter(pk=line_id)
            except (PurchaseOrderLineItem.DoesNotExist, ValueError):
                pass

        # TODO - Option to pass multiple lines?

        # No lines specified - default selection
        if lines is None:
            lines = self.order.pending_line_items()

        return lines

    def get(self, request, *args, **kwargs):
        """ Respond to a GET request. Determines which parts are outstanding,
        and presents a list of these parts to the user.
        """

        self.request = request
        self.order = get_object_or_404(PurchaseOrder, pk=self.kwargs['pk'])

        self.lines = self.get_lines()

        for line in self.lines:
            # Pre-fill the remaining quantity
            line.receive_quantity = line.remaining()

        return self.renderJsonResponse(request, form=self.get_form())

    def post(self, request, *args, **kwargs):
        """ Respond to a POST request. Data checking and error handling.
        If the request is valid, new StockItem objects will be made
        for each received item.
        """

        self.request = request
        self.order = get_object_or_404(PurchaseOrder, pk=self.kwargs['pk'])

        self.lines = []
        self.destination = None

        msg = _("Items received")

        # Extract the destination for received parts
        if 'location' in request.POST:
            pk = request.POST['location']
            try:
                self.destination = StockLocation.objects.get(id=pk)
            except (StockLocation.DoesNotExist, ValueError):
                pass

        errors = False

        if self.destination is None:
            errors = True
            msg = _("No destination set")

        # Extract information on all submitted line items
        for item in request.POST:
            if item.startswith('line-'):
                pk = item.replace('line-', '')

                try:
                    line = PurchaseOrderLineItem.objects.get(id=pk)
                except (PurchaseOrderLineItem.DoesNotExist, ValueError):
                    continue

                # Check that the StockStatus was set
                status_key = 'status-{pk}'.format(pk=pk)
                status = request.POST.get(status_key, StockStatus.OK)

                try:
                    status = int(status)
                except ValueError:
                    status = StockStatus.OK

                if status in StockStatus.RECEIVING_CODES:
                    line.status_code = status
                else:
                    line.status_code = StockStatus.OK

                # Check that line matches the order
                if not line.order == self.order:
                    # TODO - Display a non-field error?
                    continue

                # Ignore a part that doesn't map to a SupplierPart
                try:
                    if line.part is None:
                        continue
                except SupplierPart.DoesNotExist:
                    continue

                receive = self.request.POST[item]

                try:
                    receive = Decimal(receive)
                except InvalidOperation:
                    # In the case on an invalid input, reset to default
                    receive = line.remaining()
                    msg = _("Error converting quantity to number")
                    errors = True

                if receive < 0:
                    receive = 0
                    errors = True
                    msg = _("Receive quantity less than zero")

                line.receive_quantity = receive
                self.lines.append(line)

        if len(self.lines) == 0:
            msg = _("No lines specified")
            errors = True

        # No errors? Receive the submitted parts!
        if errors is False:
            self.receive_parts()

        data = {
            'form_valid': errors is False,
            'success': msg,
        }

        return self.renderJsonResponse(request, data=data, form=self.get_form())

    @transaction.atomic
    def receive_parts(self):
        """ Called once the form has been validated.
        Create new stockitems against received parts.
        """

        for line in self.lines:

            if not line.part:
                continue

            self.order.receive_line_item(
                line,
                self.destination,
                line.receive_quantity,
                self.request.user,
                status=line.status_code,
            )


class OrderParts(AjaxView):
    """ View for adding various SupplierPart items to a Purchase Order.

    SupplierParts can be selected from a variety of 'sources':

    - ?supplier_parts[]= -> Direct list of SupplierPart objects
    - ?parts[]= -> List of base Part objects (user must then select supplier parts)
    - ?stock[]= -> List of StockItem objects (user must select supplier parts)
    - ?build= -> A Build object (user must select parts, then supplier parts)

    """

    ajax_form_title = _("Order Parts")
    ajax_template_name = 'order/order_wizard/select_parts.html'

    role_required = [
        'part.view',
        'purchase_order.change',
    ]

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

                # Attempt to auto-select a purchase order
                orders = PurchaseOrder.objects.filter(supplier=supplier, status__in=PurchaseOrderStatus.OPEN)

                if orders.count() == 1:
                    supplier.selected_purchase_order = orders.first().id
                else:
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

                parts = build.required_parts

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

    @transaction.atomic
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
    ajax_form_title = _('Add Line Item')
    role_required = 'purchase_order.add'

    def validate(self, item, form, **kwargs):

        order = form.cleaned_data.get('order', None)

        part = form.cleaned_data.get('part', None)

        if not part:
            form.add_error('part', _('Supplier part must be specified'))

        if part and order:
            if not part.supplier == order.supplier:
                form.add_error(
                    'part',
                    _('Supplier must match for Part and Order')
                )

    def get_form(self):
        """ Limit choice options based on the selected order, etc
        """

        form = super().get_form()

        # Limit the available to orders to ones that are PENDING
        query = form.fields['order'].queryset
        query = query.filter(status=PurchaseOrderStatus.PENDING)
        form.fields['order'].queryset = query

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
        except (ValueError, PurchaseOrder.DoesNotExist):
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

            except (PurchaseOrder.DoesNotExist, ValueError):
                pass

        return initials


class SOLineItemCreate(AjaxCreateView):
    """ Ajax view for creating a new SalesOrderLineItem object """

    model = SalesOrderLineItem
    context_order_name = 'line'
    form_class = order_forms.EditSalesOrderLineItemForm
    ajax_form_title = _('Add Line Item')
    role_required = 'sales_order.add'

    def get_form(self, *args, **kwargs):

        form = super().get_form(*args, **kwargs)

        # If the order is specified, hide the widget
        order_id = form['order'].value()

        if SalesOrder.objects.filter(id=order_id).exists():
            form.fields['order'].widget = HiddenInput()

        return form

    def get_initial(self):
        """
        Extract initial data for this line item:

        Options:
            order: The SalesOrder object
            part: The Part object
        """

        initials = super().get_initial().copy()

        order_id = self.request.GET.get('order', None)
        part_id = self.request.GET.get('part', None)

        if order_id:
            try:
                order = SalesOrder.objects.get(id=order_id)
                initials['order'] = order
            except (SalesOrder.DoesNotExist, ValueError):
                pass

        if part_id:
            try:
                part = Part.objects.get(id=part_id)
                if part.salable:
                    initials['part'] = part
            except (Part.DoesNotExist, ValueError):
                pass

        return initials


class SOLineItemEdit(AjaxUpdateView):
    """ View for editing a SalesOrderLineItem """

    model = SalesOrderLineItem
    form_class = order_forms.EditSalesOrderLineItemForm
    ajax_form_title = _('Edit Line Item')
    role_required = 'sales_order.change'

    def get_form(self):
        form = super().get_form()

        form.fields.pop('order')
        form.fields.pop('part')

        return form


class POLineItemEdit(AjaxUpdateView):
    """ View for editing a PurchaseOrderLineItem object in a modal form.
    """

    model = PurchaseOrderLineItem
    form_class = order_forms.EditPurchaseOrderLineItemForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = _('Edit Line Item')
    role_required = 'purchase_order.change'

    def get_form(self):
        form = super().get_form()

        # Prevent user from editing order once line item is assigned
        form.fields['order'].widget = HiddenInput()

        return form


class POLineItemDelete(AjaxDeleteView):
    """ View for deleting a PurchaseOrderLineItem object in a modal form
    """

    model = PurchaseOrderLineItem
    ajax_form_title = _('Delete Line Item')
    ajax_template_name = 'order/po_lineitem_delete.html'
    role_required = 'purchase_order.delete'

    def get_data(self):
        return {
            'danger': _('Deleted line item'),
        }


class SOLineItemDelete(AjaxDeleteView):

    model = SalesOrderLineItem
    ajax_form_title = _("Delete Line Item")
    ajax_template_name = "order/so_lineitem_delete.html"
    role_required = 'sales_order.delete'

    def get_data(self):
        return {
            'danger': _('Deleted line item'),
        }


class SalesOrderAllocationCreate(AjaxCreateView):
    """ View for creating a new SalesOrderAllocation """

    model = SalesOrderAllocation
    form_class = order_forms.EditSalesOrderAllocationForm
    ajax_form_title = _('Allocate Stock to Order')
    role_required = 'sales_order.add'

    def get_initial(self):
        initials = super().get_initial().copy()

        line_id = self.request.GET.get('line', None)

        if line_id is not None:
            line = SalesOrderLineItem.objects.get(pk=line_id)

            initials['line'] = line

            # Search for matching stock items, pre-fill if there is only one
            items = StockItem.objects.filter(part=line.part)

            quantity = line.quantity - line.allocated_quantity()
            
            if quantity < 0:
                quantity = 0
        
            if items.count() == 1:
                item = items.first()
                initials['item'] = item

                # Reduce the quantity IF there is not enough stock
                qmax = item.quantity - item.allocation_count()

                if qmax < quantity:
                    quantity = qmax

            initials['quantity'] = quantity

        return initials

    def get_form(self):
        
        form = super().get_form()

        line_id = form['line'].value()

        # If a line item has been specified, reduce the queryset for the stockitem accordingly
        try:
            line = SalesOrderLineItem.objects.get(pk=line_id)

            # Construct a queryset for allowable stock items
            queryset = StockItem.objects.filter(StockItem.IN_STOCK_FILTER)

            # Ensure the part reference matches
            queryset = queryset.filter(part=line.part)

            # Exclude StockItem which are already allocated to this order
            allocated = [allocation.item.pk for allocation in line.allocations.all()]

            queryset = queryset.exclude(pk__in=allocated)

            # Exclude stock items which have expired
            if not InvenTreeSetting.get_setting('STOCK_ALLOW_EXPIRED_SALE'):
                queryset = queryset.exclude(StockItem.EXPIRED_FILTER)

            form.fields['item'].queryset = queryset

            # Hide the 'line' field
            form.fields['line'].widget = HiddenInput()
        
        except (ValueError, SalesOrderLineItem.DoesNotExist):
            pass
        
        return form


class SalesOrderAllocationEdit(AjaxUpdateView):

    model = SalesOrderAllocation
    form_class = order_forms.EditSalesOrderAllocationForm
    ajax_form_title = _('Edit Allocation Quantity')
    role_required = 'sales_order.change'

    def get_form(self):
        form = super().get_form()

        # Prevent the user from editing particular fields
        form.fields.pop('item')
        form.fields.pop('line')

        return form


class SalesOrderAllocationDelete(AjaxDeleteView):

    model = SalesOrderAllocation
    ajax_form_title = _("Remove allocation")
    context_object_name = 'allocation'
    ajax_template_name = "order/so_allocation_delete.html"
    role_required = 'sales_order.delete'
