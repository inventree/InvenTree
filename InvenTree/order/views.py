"""Django views for interacting with Order app."""

import logging
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import permission_required
from django.db.utils import IntegrityError
from django.forms import HiddenInput, IntegerField
from django.http import HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from django_ical.views import ICalFeed

from common.files import FileManager
from common.forms import MatchFieldForm, UploadFileForm
from common.models import InvenTreeSetting
from common.settings import settings
from common.views import FileManagementFormView
from company.models import SupplierPart  # ManufacturerPart
from InvenTree.helpers import DownloadFile
from InvenTree.views import AjaxView, InvenTreeRoleMixin
from part.models import Part
from part.views import PartPricing
from plugin.views import InvenTreePluginViewMixin

from . import forms as order_forms
from .admin import PurchaseOrderLineItemResource, SalesOrderLineItemResource
from .models import (PurchaseOrder, PurchaseOrderLineItem, SalesOrder,
                     SalesOrderLineItem)

logger = logging.getLogger("inventree")


class PurchaseOrderIndex(InvenTreeRoleMixin, ListView):
    """List view for all purchase orders."""

    model = PurchaseOrder
    template_name = 'order/purchase_orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        """Retrieve the list of purchase orders, ensure that the most recent ones are returned first."""
        queryset = PurchaseOrder.objects.all().order_by('-creation_date')

        return queryset


class SalesOrderIndex(InvenTreeRoleMixin, ListView):
    """SalesOrder index (list) view class"""
    model = SalesOrder
    template_name = 'order/sales_orders.html'
    context_object_name = 'orders'


class PurchaseOrderDetail(InvenTreeRoleMixin, InvenTreePluginViewMixin, DetailView):
    """Detail view for a PurchaseOrder object."""

    context_object_name = 'order'
    queryset = PurchaseOrder.objects.all().prefetch_related('lines')
    template_name = 'order/purchase_order_detail.html'


class SalesOrderDetail(InvenTreeRoleMixin, InvenTreePluginViewMixin, DetailView):
    """Detail view for a SalesOrder object."""

    context_object_name = 'order'
    queryset = SalesOrder.objects.all().prefetch_related('lines__allocations__item__purchase_order')
    template_name = 'order/sales_order_detail.html'


class PurchaseOrderUpload(FileManagementFormView):
    """PurchaseOrder: Upload file, match to fields and parts (using multi-Step form)"""

    class OrderFileManager(FileManager):
        """Specify required fields"""
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
        """Get order or return 404."""
        return get_object_or_404(PurchaseOrder, pk=self.kwargs['pk'])

    def get_context_data(self, form, **kwargs):
        """Handle context data for order."""
        context = super().get_context_data(form=form, **kwargs)

        order = self.get_order()

        context.update({'order': order})

        return context

    def get_field_selection(self):
        """Once data columns have been selected, attempt to pre-select the proper data from the database.

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
        """Once all the data is in, process it to add PurchaseOrderLineItem instances to the order."""
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
    """Export a sales order.

    - File format can optionally be passed as a query parameter e.g. ?format=CSV
    - Default file format is CSV
    """

    model = SalesOrder

    role_required = 'sales_order.view'

    def get(self, request, *args, **kwargs):
        """Perform GET request to export SalesOrder dataset"""
        order = get_object_or_404(SalesOrder, pk=self.kwargs.get('pk', None))

        export_format = request.GET.get('format', 'csv')

        filename = f"{str(order)} - {order.customer.name}.{export_format}"

        dataset = SalesOrderLineItemResource().export(queryset=order.lines.all())

        filedata = dataset.export(format=export_format)

        return DownloadFile(filedata, filename)


class PurchaseOrderExport(AjaxView):
    """File download for a purchase order.

    - File format can be optionally passed as a query param e.g. ?format=CSV
    - Default file format is CSV
    """

    model = PurchaseOrder

    # Specify role as we cannot introspect from "AjaxView"
    role_required = 'purchase_order.view'

    def get(self, request, *args, **kwargs):
        """Perform GET request to export PurchaseOrder dataset"""
        order = get_object_or_404(PurchaseOrder, pk=self.kwargs.get('pk', None))

        export_format = request.GET.get('format', 'csv')

        filename = '{order} - {company}.{fmt}'.format(
            order=str(order),
            company=order.supplier.name,
            fmt=export_format
        )

        dataset = PurchaseOrderLineItemResource().export(queryset=order.lines.all())

        filedata = dataset.export(format=export_format)

        return DownloadFile(filedata, filename)


class LineItemPricing(PartPricing):
    """View for inspecting part pricing information."""

    class EnhancedForm(PartPricing.form_class):
        """Extra form options"""
        pk = IntegerField(widget=HiddenInput())
        so_line = IntegerField(widget=HiddenInput())

    form_class = EnhancedForm

    def get_part(self, id=False):
        """Return the Part instance associated with this view"""
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
        """Return the SalesOrderLineItem associated with this view"""
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
        """Return set quantity in decimal format."""
        qty = Decimal(self.request.GET.get('quantity', 1))
        if qty == 1:
            return Decimal(self.request.POST.get('quantity', 1))
        return qty

    def get_initials(self):
        """Return initial context values for this view"""
        initials = super().get_initials()
        initials['pk'] = self.get_part(id=True)
        initials['so_line'] = self.get_so(pk=True)
        return initials

    def post(self, request, *args, **kwargs):
        """Respond to a POST request to get particular pricing information"""
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


@permission_required('orders.view')
class PurchaseOrderCalendarExport(ICalFeed):
    """Calendar export for Purchase Orders

    Optional parameters:
    -
    """

    # Parameters for the whole calendar
    title = f'{InvenTreeSetting.get_setting("INVENTREE_COMPANY_NAME")} {_("Purchase Orders")}'
    instance_url = InvenTreeSetting.get_setting("INVENTREE_BASE_URL").replace("http://", "").replace("https://", "")
    product_id = f'//{instance_url}//{title}//EN'
    timezone = settings.TIME_ZONE
    file_name = "calendar.ics"

    def __init__(self, *args, **kwargs):
        """Initialization routine for the calendar exporter"""

        # Send to ICalFeed without arguments
        super().__init__()

    def items(self):
        """Return a list of PurchaseOrders.

        Filters:
        - Only return those which have a target_date set
        """
        return PurchaseOrder.objects.filter(target_date__isnull=False)

    def item_title(self, item):
        """Set the event title to the purchase order reference"""
        return item.reference

    def item_description(self, item):
        """Set the event description"""
        return item.description

    def item_start_datetime(self, item):
        """Set event start to target date. Goal is all-day event."""
        return item.target_date

    def item_end_datetime(self, item):
        """Set event end to target date. Goal is all-day event."""
        return item.target_date

    def item_created(self, item):
        """Use creation date of PO as creation date of event."""
        return item.creation_date

    def item_class(self, item):
        """Set item class to PUBLIC"""
        return 'PUBLIC'

    def item_guid(self, item):
        """Return globally unique UID for event"""
        return f'po_{item.pk}_{item.reference.replace(" ","-")}@{self.instance_url}'

    def item_link(self, item):
        """Set the item link."""
        site_url = InvenTreeSetting.get_setting("INVENTREE_BASE_URL")
        return f'{site_url}{item.get_absolute_url()}'


so_calender_view = permission_required('orders.view')(PurchaseOrderCalendarExport())
