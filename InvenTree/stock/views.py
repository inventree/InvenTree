"""Django views for interacting with Stock app."""

from datetime import datetime

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

import common.settings
from InvenTree.forms import ConfirmForm
from InvenTree.helpers import str2bool
from InvenTree.views import (AjaxCreateView, AjaxDeleteView, AjaxUpdateView,
                             InvenTreeRoleMixin, QRCodeView)
from plugin.views import InvenTreePluginViewMixin

from . import forms as StockForms
from .models import StockItem, StockItemTracking, StockLocation


class StockIndex(InvenTreeRoleMixin, InvenTreePluginViewMixin, ListView):
    """StockIndex view loads all StockLocation and StockItem object."""
    model = StockItem
    template_name = 'stock/location.html'
    context_obect_name = 'locations'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs).copy()

        # Return all top-level locations
        locations = StockLocation.objects.filter(parent=None)

        context['locations'] = locations
        context['items'] = StockItem.objects.all()

        context['loc_count'] = StockLocation.objects.count()
        context['stock_count'] = StockItem.objects.count()

        # No 'ownership' checks are necessary for the top-level StockLocation view
        context['user_owns_location'] = True
        context['location_owner'] = None
        context['ownership_enabled'] = common.models.InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')

        return context


class StockLocationDetail(InvenTreeRoleMixin, InvenTreePluginViewMixin, DetailView):
    """Detailed view of a single StockLocation object."""

    context_object_name = 'location'
    template_name = 'stock/location.html'
    queryset = StockLocation.objects.all()
    model = StockLocation

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['ownership_enabled'] = common.models.InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')
        context['location_owner'] = context['location'].get_location_owner()
        context['user_owns_location'] = context['location'].check_ownership(self.request.user)

        return context


class StockItemDetail(InvenTreeRoleMixin, InvenTreePluginViewMixin, DetailView):
    """Detailed view of a single StockItem object."""

    context_object_name = 'item'
    template_name = 'stock/item.html'
    queryset = StockItem.objects.all()
    model = StockItem

    def get_context_data(self, **kwargs):
        """Add information on the "next" and "previous" StockItem objects, based on the serial numbers."""
        data = super().get_context_data(**kwargs)

        if self.object.serialized:
            data['previous'] = self.object.get_next_serialized_item(reverse=True)
            data['next'] = self.object.get_next_serialized_item()

        data['ownership_enabled'] = common.models.InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')
        data['item_owner'] = self.object.get_item_owner()
        data['user_owns_item'] = self.object.check_ownership(self.request.user)

        # Allocation information
        data['allocated_to_sales_orders'] = self.object.sales_order_allocation_count()
        data['allocated_to_build_orders'] = self.object.build_allocation_count()
        data['allocated_to_orders'] = data['allocated_to_sales_orders'] + data['allocated_to_build_orders']
        data['available'] = max(0, self.object.quantity - data['allocated_to_orders'])

        return data

    def get(self, request, *args, **kwargs):
        """Check if item exists else return to stock index."""
        stock_pk = kwargs.get('pk', None)

        if stock_pk:
            try:
                stock_item = StockItem.objects.get(pk=stock_pk)
            except StockItem.DoesNotExist:
                stock_item = None

            if not stock_item:
                return HttpResponseRedirect(reverse('stock-index'))

        return super().get(request, *args, **kwargs)


class StockLocationQRCode(QRCodeView):
    """View for displaying a QR code for a StockLocation object."""

    ajax_form_title = _("Stock Location QR code")

    role_required = ['stock_location.view', 'stock.view']

    def get_qr_data(self):
        """Generate QR code data for the StockLocation."""
        try:
            loc = StockLocation.objects.get(id=self.pk)
            return loc.format_barcode()
        except StockLocation.DoesNotExist:
            return None


class StockItemReturnToStock(AjaxUpdateView):
    """View for returning a stock item (which is assigned to a customer) to stock."""

    model = StockItem
    ajax_form_title = _("Return to Stock")
    context_object_name = "item"
    form_class = StockForms.ReturnStockItemForm

    def validate(self, item, form, **kwargs):

        location = form.cleaned_data.get('location', None)

        if not location:
            form.add_error('location', _('Specify a valid location'))

    def save(self, item, form, **kwargs):

        location = form.cleaned_data.get('location', None)

        if location:
            item.returnFromCustomer(location, self.request.user)

    def get_data(self):
        return {
            'success': _('Stock item returned from customer')
        }


class StockItemDeleteTestData(AjaxUpdateView):
    """View for deleting all test data."""

    model = StockItem
    form_class = ConfirmForm
    ajax_form_title = _("Delete All Test Data")

    role_required = ['stock.change', 'stock.delete']

    def get_form(self):
        return ConfirmForm()

    def post(self, request, *args, **kwargs):

        valid = False

        stock_item = StockItem.objects.get(pk=self.kwargs['pk'])
        form = self.get_form()

        confirm = str2bool(request.POST.get('confirm', False))

        if confirm is not True:
            form.add_error('confirm', _('Confirm test data deletion'))
            form.add_error(None, _('Check the confirmation box'))
        else:
            stock_item.test_results.all().delete()
            valid = True

        data = {
            'form_valid': valid,
        }

        return self.renderJsonResponse(request, form, data)


class StockItemQRCode(QRCodeView):
    """View for displaying a QR code for a StockItem object."""

    ajax_form_title = _("Stock Item QR Code")
    role_required = 'stock.view'

    def get_qr_data(self):
        """Generate QR code data for the StockItem."""
        try:
            item = StockItem.objects.get(id=self.pk)
            return item.format_barcode()
        except StockItem.DoesNotExist:
            return None


class StockItemConvert(AjaxUpdateView):
    """View for 'converting' a StockItem to a variant of its current part."""

    model = StockItem
    form_class = StockForms.ConvertStockItemForm
    ajax_form_title = _('Convert Stock Item')
    ajax_template_name = 'stock/stockitem_convert.html'
    context_object_name = 'item'

    def get_form(self):
        """Filter the available parts."""
        form = super().get_form()
        item = self.get_object()

        form.fields['part'].queryset = item.part.get_conversion_options()

        return form

    def save(self, obj, form):

        stock_item = self.get_object()

        variant = form.cleaned_data.get('part', None)

        stock_item.convert_to_variant(variant, user=self.request.user)

        return stock_item


class StockLocationDelete(AjaxDeleteView):
    """View to delete a StockLocation.

    Presents a deletion confirmation form to the user
    """

    model = StockLocation
    success_url = '/stock'
    ajax_template_name = 'stock/location_delete.html'
    context_object_name = 'location'
    ajax_form_title = _('Delete Stock Location')


class StockItemDelete(AjaxDeleteView):
    """View to delete a StockItem.

    Presents a deletion confirmation form to the user
    """

    model = StockItem
    success_url = '/stock/'
    ajax_template_name = 'stock/item_delete.html'
    context_object_name = 'item'
    ajax_form_title = _('Delete Stock Item')


class StockItemTrackingDelete(AjaxDeleteView):
    """View to delete a StockItemTracking object.

    Presents a deletion confirmation form to the user
    """

    model = StockItemTracking
    ajax_template_name = 'stock/tracking_delete.html'
    ajax_form_title = _('Delete Stock Tracking Entry')


class StockItemTrackingEdit(AjaxUpdateView):
    """View for editing a StockItemTracking object."""

    model = StockItemTracking
    ajax_form_title = _('Edit Stock Tracking Entry')
    form_class = StockForms.TrackingEntryForm


class StockItemTrackingCreate(AjaxCreateView):
    """View for creating a new StockItemTracking object."""

    model = StockItemTracking
    ajax_form_title = _("Add Stock Tracking Entry")
    form_class = StockForms.TrackingEntryForm

    def post(self, request, *args, **kwargs):

        self.request = request
        self.form = self.get_form()

        valid = False

        if self.form.is_valid():
            stock_id = self.kwargs['pk']

            if stock_id:
                try:
                    stock_item = StockItem.objects.get(id=stock_id)

                    # Save new tracking information
                    tracking = self.form.save(commit=False)
                    tracking.item = stock_item
                    tracking.user = self.request.user
                    tracking.quantity = stock_item.quantity
                    tracking.date = datetime.now().date()
                    tracking.system = False

                    tracking.save()

                    valid = True

                except (StockItem.DoesNotExist, ValueError):
                    pass

        data = {
            'form_valid': valid
        }

        return self.renderJsonResponse(request, self.form, data=data)
