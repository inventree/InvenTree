"""
Django views for interacting with Order app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import transaction
from django.db.utils import IntegrityError
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormMixin
from django.forms import HiddenInput, IntegerField

import logging
from decimal import Decimal, InvalidOperation

from .models import PurchaseOrder, PurchaseOrderLineItem
from .models import SalesOrder, SalesOrderLineItem
from .models import SalesOrderAllocation
from .admin import POLineItemResource, SOLineItemResource
from build.models import Build
from company.models import Company, SupplierPart  # ManufacturerPart
from stock.models import StockItem
from part.models import Part

from common.forms import UploadFileForm, MatchFieldForm
from common.views import FileManagementFormView
from common.files import FileManager

from . import forms as order_forms
from part.views import PartPricing

from InvenTree.views import AjaxView, AjaxUpdateView
from InvenTree.helpers import DownloadFile, str2bool
from InvenTree.helpers import extract_serial_numbers
from InvenTree.views import InvenTreeRoleMixin

from InvenTree.status_codes import PurchaseOrderStatus


logger = logging.getLogger("inventree")


class PurchaseOrderIndex(InvenTreeRoleMixin, ListView):
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

        return ctx


class SalesOrderIndex(InvenTreeRoleMixin, ListView):

    model = SalesOrder
    template_name = 'order/sales_orders.html'
    context_object_name = 'orders'


class PurchaseOrderDetail(InvenTreeRoleMixin, DetailView):
    """ Detail view for a PurchaseOrder object """

    context_object_name = 'order'
    queryset = PurchaseOrder.objects.all().prefetch_related('lines')
    template_name = 'order/purchase_order_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        return ctx


class SalesOrderDetail(InvenTreeRoleMixin, DetailView):
    """ Detail view for a SalesOrder object """

    context_object_name = 'order'
    queryset = SalesOrder.objects.all().prefetch_related('lines__allocations__item__purchase_order')
    template_name = 'order/sales_order_detail.html'


class PurchaseOrderCancel(AjaxUpdateView):
    """ View for cancelling a purchase order """

    model = PurchaseOrder
    ajax_form_title = _('Cancel Order')
    ajax_template_name = 'order/order_cancel.html'
    form_class = order_forms.CancelPurchaseOrderForm

    def validate(self, order, form, **kwargs):

        confirm = str2bool(form.cleaned_data.get('confirm', False))

        if not confirm:
            form.add_error('confirm', _('Confirm order cancellation'))

        if not order.can_cancel():
            form.add_error(None, _('Order cannot be cancelled'))

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


class PurchaseOrderUpload(FileManagementFormView):
    ''' PurchaseOrder: Upload file, match to fields and parts (using multi-Step form) '''

    class OrderFileManager(FileManager):
        REQUIRED_HEADERS = [
            'Quantity',
        ]

        ITEM_MATCH_HEADERS = [
            'Manufacturer_MPN',
            'Supplier_SKU',
        ]

        OPTIONAL_HEADERS = [
            'Purchase_Price',
            'Reference',
            'Notes',
        ]

    name = 'order'
    form_list = [
        ('upload', UploadFileForm),
        ('fields', MatchFieldForm),
        ('items', order_forms.OrderMatchItemForm),
    ]
    form_steps_template = [
        'order/order_wizard/po_upload.html',
        'order/order_wizard/match_fields.html',
        'order/order_wizard/match_parts.html',
    ]
    form_steps_description = [
        _("Upload File"),
        _("Match Fields"),
        _("Match Supplier Parts"),
    ]
    form_field_map = {
        'item_select': 'part',
        'quantity': 'quantity',
        'purchase_price': 'purchase_price',
        'reference': 'reference',
        'notes': 'notes',
    }
    file_manager_class = OrderFileManager

    def get_order(self):
        """ Get order or return 404 """

        return get_object_or_404(PurchaseOrder, pk=self.kwargs['pk'])

    def get_context_data(self, form, **kwargs):
        """ Handle context data for order """

        context = super().get_context_data(form=form, **kwargs)

        order = self.get_order()

        context.update({'order': order})

        return context

    def get_field_selection(self):
        """ Once data columns have been selected, attempt to pre-select the proper data from the database.
        This function is called once the field selection has been validated.
        The pre-fill data are then passed through to the SupplierPart selection form.
        """

        order = self.get_order()

        self.allowed_items = SupplierPart.objects.filter(supplier=order.supplier).prefetch_related('manufacturer_part')

        # Fields prefixed with "Part_" can be used to do "smart matching" against Part objects in the database
        q_idx = self.get_column_index('Quantity')
        s_idx = self.get_column_index('Supplier_SKU')
        m_idx = self.get_column_index('Manufacturer_MPN')
        p_idx = self.get_column_index('Purchase_Price')
        r_idx = self.get_column_index('Reference')
        n_idx = self.get_column_index('Notes')

        for row in self.rows:

            # Initially use a quantity of zero
            quantity = Decimal(0)

            # Initially we do not have a part to reference
            exact_match_part = None

            # Check if there is a column corresponding to "quantity"
            if q_idx >= 0:
                q_val = row['data'][q_idx]['cell']

                if q_val:
                    # Delete commas
                    q_val = q_val.replace(',', '')

                    try:
                        # Attempt to extract a valid quantity from the field
                        quantity = Decimal(q_val)
                        # Store the 'quantity' value
                        row['quantity'] = quantity
                    except (ValueError, InvalidOperation):
                        pass

            # Check if there is a column corresponding to "Supplier SKU"
            if s_idx >= 0:
                sku = row['data'][s_idx]['cell']

                try:
                    # Attempt SupplierPart lookup based on SKU value
                    exact_match_part = self.allowed_items.get(SKU__contains=sku)
                except (ValueError, SupplierPart.DoesNotExist, SupplierPart.MultipleObjectsReturned):
                    exact_match_part = None

            # Check if there is a column corresponding to "Manufacturer MPN" and no exact match found yet
            if m_idx >= 0 and not exact_match_part:
                mpn = row['data'][m_idx]['cell']

                try:
                    # Attempt SupplierPart lookup based on MPN value
                    exact_match_part = self.allowed_items.get(manufacturer_part__MPN__contains=mpn)
                except (ValueError, SupplierPart.DoesNotExist, SupplierPart.MultipleObjectsReturned):
                    exact_match_part = None

            # Supply list of part options for each row, sorted by how closely they match the part name
            row['item_options'] = self.allowed_items

            # Unless found, the 'part_match' is blank
            row['item_match'] = None

            if exact_match_part:
                # If there is an exact match based on SKU or MPN, use that
                row['item_match'] = exact_match_part

            # Check if there is a column corresponding to "purchase_price"
            if p_idx >= 0:
                p_val = row['data'][p_idx]['cell']

                if p_val:
                    row['purchase_price'] = p_val

            # Check if there is a column corresponding to "reference"
            if r_idx >= 0:
                reference = row['data'][r_idx]['cell']
                row['reference'] = reference

            # Check if there is a column corresponding to "notes"
            if n_idx >= 0:
                notes = row['data'][n_idx]['cell']
                row['notes'] = notes

    def done(self, form_list, **kwargs):
        """ Once all the data is in, process it to add PurchaseOrderLineItem instances to the order """

        order = self.get_order()
        items = self.get_clean_items()

        # Create PurchaseOrderLineItem instances
        for purchase_order_item in items.values():
            try:
                supplier_part = SupplierPart.objects.get(pk=int(purchase_order_item['part']))
            except (ValueError, SupplierPart.DoesNotExist):
                continue

            quantity = purchase_order_item.get('quantity', 0)
            if quantity:
                purchase_order_line_item = PurchaseOrderLineItem(
                    order=order,
                    part=supplier_part,
                    quantity=quantity,
                    purchase_price=purchase_order_item.get('purchase_price', None),
                    reference=purchase_order_item.get('reference', ''),
                    notes=purchase_order_item.get('notes', ''),
                )
                try:
                    purchase_order_line_item.save()
                except IntegrityError:
                    # PurchaseOrderLineItem already exists
                    pass

        return HttpResponseRedirect(reverse('po-detail', kwargs={'pk': self.kwargs['pk']}))


class SalesOrderExport(AjaxView):
    """
    Export a sales order

    - File format can optionally be passed as a query parameter e.g. ?format=CSV
    - Default file format is CSV
    """

    model = SalesOrder

    role_required = 'sales_order.view'

    def get(self, request, *args, **kwargs):

        order = get_object_or_404(SalesOrder, pk=self.kwargs.get('pk', None))

        export_format = request.GET.get('format', 'csv')

        filename = f"{str(order)} - {order.customer.name}.{export_format}"

        dataset = SOLineItemResource().export(queryset=order.lines.all())

        filedata = dataset.export(format=export_format)

        return DownloadFile(filedata, filename)


class PurchaseOrderExport(AjaxView):
    """ File download for a purchase order

    - File format can be optionally passed as a query param e.g. ?format=CSV
    - Default file format is CSV
    """

    model = PurchaseOrder

    # Specify role as we cannot introspect from "AjaxView"
    role_required = 'purchase_order.view'

    def get(self, request, *args, **kwargs):

        order = get_object_or_404(PurchaseOrder, pk=self.kwargs.get('pk', None))

        export_format = request.GET.get('format', 'csv')

        filename = '{order} - {company}.{fmt}'.format(
            order=str(order),
            company=order.supplier.name,
            fmt=export_format
        )

        dataset = POLineItemResource().export(queryset=order.lines.all())

        filedata = dataset.export(format=export_format)

        return DownloadFile(filedata, filename)


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

    def get_data(self):
        """ enrich respone json data """
        data = super().get_data()
        # if in selection-phase, add a button to update the prices
        if getattr(self, 'form_step', 'select_parts') == 'select_parts':
            data['buttons'] = [{'name': 'update_price', 'title': _('Update prices')}]  # set buttons
            data['hideErrorMessage'] = '1'  # hide the error message
        return data

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

                # set supplier-price
                if supplier_part:
                    supplier_price = supplier_part.get_price(quantity)
                    if supplier_price:
                        part.purchase_price = supplier_price / quantity
                if not hasattr(part, 'purchase_price'):
                    part.purchase_price = None

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
            # No errors? and the price-update button was not used to submit? Proceed to PO selection form
            if part_errors is False and 'act-btn_update_price' not in request.POST:
                self.ajax_template_name = 'order/order_wizard/select_pos.html'
                self.form_step = 'select_purchase_orders'  # set step (important for get_data)

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
            'success': _('Ordered {n} parts').format(n=len(self.parts))
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

                # get purchase price
                purchase_price = item.purchase_price

                order.add_line_item(supplier_part, quantity, purchase_price=purchase_price)



#### TODO: This class MUST be converted to the API forms!
#### TODO: We MUST select the shipment
class SalesOrderAssignSerials(AjaxView, FormMixin):
    """
    View for assigning stock items to a sales order,
    by serial number lookup.
    """

    model = SalesOrderAllocation
    role_required = 'sales_order.change'
    ajax_template_name = 'order/so_allocate_by_serial.html'
    ajax_form_title = _('Allocate Serial Numbers')
    form_class = order_forms.AllocateSerialsToSalesOrderForm

    # Keep track of SalesOrderLineItem and Part references
    line = None
    part = None

    def get_initial(self):
        """
        Initial values are passed as query params
        """

        initials = super().get_initial()

        try:
            self.line = SalesOrderLineItem.objects.get(pk=self.request.GET.get('line', None))
            initials['line'] = self.line
        except (ValueError, SalesOrderLineItem.DoesNotExist):
            pass

        try:
            self.part = Part.objects.get(pk=self.request.GET.get('part', None))
            initials['part'] = self.part
        except (ValueError, Part.DoesNotExist):
            pass

        return initials

    def post(self, request, *args, **kwargs):

        self.form = self.get_form()

        # Validate the form
        self.form.is_valid()
        self.validate()

        valid = self.form.is_valid()

        if valid:
            self.allocate_items()

        data = {
            'form_valid': valid,
            'form_errors': self.form.errors.as_json(),
            'non_field_errors': self.form.non_field_errors().as_json(),
            'success': _("Allocated {n} items").format(n=len(self.stock_items))
        }

        return self.renderJsonResponse(request, self.form, data)

    def validate(self):

        data = self.form.cleaned_data

        # Extract hidden fields from posted data
        self.line = data.get('line', None)
        self.part = data.get('part', None)

        if self.line:
            self.form.fields['line'].widget = HiddenInput()
        else:
            self.form.add_error('line', _('Select line item'))

        if self.part:
            self.form.fields['part'].widget = HiddenInput()
        else:
            self.form.add_error('part', _('Select part'))

        if not self.form.is_valid():
            return

        # Form is otherwise valid - check serial numbers
        serials = data.get('serials', '')
        quantity = data.get('quantity', 1)

        # Save a list of serial_numbers
        self.serial_numbers = None
        self.stock_items = []

        try:
            self.serial_numbers = extract_serial_numbers(serials, quantity)

            for serial in self.serial_numbers:
                try:
                    # Find matching stock item
                    stock_item = StockItem.objects.get(
                        part=self.part,
                        serial=serial
                    )
                except StockItem.DoesNotExist:
                    self.form.add_error(
                        'serials',
                        _('No matching item for serial {serial}').format(serial=serial)
                    )
                    continue

                # Now we have a valid stock item - but can it be added to the sales order?

                # If not in stock, cannot be added to the order
                if not stock_item.in_stock:
                    self.form.add_error(
                        'serials',
                        _('{serial} is not in stock').format(serial=serial)
                    )
                    continue

                # Already allocated to an order
                if stock_item.is_allocated():
                    self.form.add_error(
                        'serials',
                        _('{serial} already allocated to an order').format(serial=serial)
                    )
                    continue

                # Add it to the list!
                self.stock_items.append(stock_item)

        except ValidationError as e:
            self.form.add_error('serials', e.messages)

    def allocate_items(self):
        """
        Create stock item allocations for each selected serial number
        """

        for stock_item in self.stock_items:
            SalesOrderAllocation.objects.create(
                item=stock_item,
                line=self.line,
                quantity=1,
            )

    def get_form(self):

        form = super().get_form()

        if self.line:
            form.fields['line'].widget = HiddenInput()

        if self.part:
            form.fields['part'].widget = HiddenInput()

        return form

    def get_context_data(self):
        return {
            'line': self.line,
            'part': self.part,
        }

    def get(self, request, *args, **kwargs):

        return self.renderJsonResponse(
            request,
            self.get_form(),
            context=self.get_context_data(),
        )


class LineItemPricing(PartPricing):
    """ View for inspecting part pricing information """

    class EnhancedForm(PartPricing.form_class):
        pk = IntegerField(widget=HiddenInput())
        so_line = IntegerField(widget=HiddenInput())

    form_class = EnhancedForm

    def get_part(self, id=False):
        if 'line_item' in self.request.GET:
            try:
                part_id = self.request.GET.get('line_item')
                part = SalesOrderLineItem.objects.get(id=part_id).part
            except Part.DoesNotExist:
                return None
        elif 'pk' in self.request.POST:
            try:
                part_id = self.request.POST.get('pk')
                part = Part.objects.get(id=part_id)
            except Part.DoesNotExist:
                return None
        else:
            return None

        if id:
            return part.id
        return part

    def get_so(self, pk=False):
        so_line = self.request.GET.get('line_item', None)
        if not so_line:
            so_line = self.request.POST.get('so_line', None)

        if so_line:
            try:
                sales_order = SalesOrderLineItem.objects.get(pk=so_line)
                if pk:
                    return sales_order.pk
                return sales_order
            except Part.DoesNotExist:
                return None
        return None

    def get_quantity(self):
        """ Return set quantity in decimal format """
        qty = Decimal(self.request.GET.get('quantity', 1))
        if qty == 1:
            return Decimal(self.request.POST.get('quantity', 1))
        return qty

    def get_initials(self):
        initials = super().get_initials()
        initials['pk'] = self.get_part(id=True)
        initials['so_line'] = self.get_so(pk=True)
        return initials

    def post(self, request, *args, **kwargs):
        # parse extra actions
        REF = 'act-btn_'
        act_btn = [a.replace(REF, '') for a in self.request.POST if REF in a]

        # check if extra action was passed
        if act_btn and act_btn[0] == 'update_price':
            # get sales order
            so_line = self.get_so()
            if not so_line:
                self.data = {'non_field_errors': [_('Sales order not found')]}
            else:
                quantity = self.get_quantity()
                price = self.get_pricing(quantity).get('unit_part_price', None)

                if not price:
                    self.data = {'non_field_errors': [_('Price not found')]}
                else:
                    # set normal update note
                    note = _('Updated {part} unit-price to {price}')

                    # check qunatity and update if different
                    if so_line.quantity != quantity:
                        so_line.quantity = quantity
                        note = _('Updated {part} unit-price to {price} and quantity to {qty}')

                    # update sale_price
                    so_line.sale_price = price
                    so_line.save()

                    # parse response
                    data = {
                        'form_valid': True,
                        'success': note.format(part=str(so_line.part), price=str(so_line.sale_price), qty=quantity)
                    }
                    return JsonResponse(data=data)

        # let the normal pricing view run
        return super().post(request, *args, **kwargs)
