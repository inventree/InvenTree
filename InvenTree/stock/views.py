"""
Django views for interacting with Stock app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import DetailView, ListView
from django.forms.models import model_to_dict
from django.forms import HiddenInput

from InvenTree.views import AjaxUpdateView, AjaxDeleteView, AjaxCreateView
from InvenTree.views import QRCodeView

from part.models import Part
from .models import StockItem, StockLocation, StockItemTracking

from .forms import EditStockLocationForm
from .forms import CreateStockItemForm
from .forms import EditStockItemForm
from .forms import MoveStockItemForm
from .forms import StocktakeForm


class StockIndex(ListView):
    """ StockIndex view loads all StockLocation and StockItem object
    """
    model = StockItem
    template_name = 'stock/location.html'
    context_obect_name = 'locations'

    def get_context_data(self, **kwargs):
        context = super(StockIndex, self).get_context_data(**kwargs).copy()

        # Return all top-level locations
        locations = StockLocation.objects.filter(parent=None)

        context['locations'] = locations
        context['items'] = StockItem.objects.all()

        return context


class StockLocationDetail(DetailView):
    """
    Detailed view of a single StockLocation object
    """

    context_object_name = 'location'
    template_name = 'stock/location.html'
    queryset = StockLocation.objects.all()
    model = StockLocation


class StockItemDetail(DetailView):
    """
    Detailed view of a single StockItem object
    """

    context_object_name = 'item'
    template_name = 'stock/item.html'
    queryset = StockItem.objects.all()
    model = StockItem


class StockLocationEdit(AjaxUpdateView):
    """
    View for editing details of a StockLocation.
    This view is used with the EditStockLocationForm to deliver a modal form to the web view
    """

    model = StockLocation
    form_class = EditStockLocationForm
    context_object_name = 'location'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Stock Location'

    def get_form(self):
        """ Customize form data for StockLocation editing.

        Limit the choices for 'parent' field to those which make sense.
        """

        form = super(AjaxUpdateView, self).get_form()

        location = self.get_object()

        # Remove any invalid choices for the 'parent' field
        parent_choices = StockLocation.objects.all()
        parent_choices = parent_choices.exclude(id__in=location.getUniqueChildren())

        form.fields['parent'].queryset = parent_choices

        return form


class StockLocationQRCode(QRCodeView):
    """ View for displaying a QR code for a StockLocation object """

    ajax_form_title = "Stock Location QR code"

    def get_qr_data(self):
        """ Generate QR code data for the StockLocation """
        try:
            loc = StockLocation.objects.get(id=self.pk)
            return loc.format_barcode()
        except StockLocation.DoesNotExist:
            return None


class StockItemQRCode(QRCodeView):
    """ View for displaying a QR code for a StockItem object """

    ajax_form_title = "Stock Item QR Code"

    def get_qr_data(self):
        """ Generate QR code data for the StockItem """
        try:
            item = StockItem.objects.get(id=self.pk)
            return item.format_barcode()
        except StockItem.DoesNotExist:
            return None
            

class StockItemEdit(AjaxUpdateView):
    """
    View for editing details of a single StockItem
    """

    model = StockItem
    form_class = EditStockItemForm
    context_object_name = 'item'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Stock Item'

    def get_form(self):
        """ Get form for StockItem editing.

        Limit the choices for supplier_part
        """

        form = super(AjaxUpdateView, self).get_form()

        item = self.get_object()

        # If the part cannot be purchased, hide the supplier_part field
        if not item.part.purchaseable:
            form.fields['supplier_part'].widget = HiddenInput()
        else:
            query = form.fields['supplier_part'].queryset
            query = query.filter(part=item.part.id)
            form.fields['supplier_part'].queryset = query

        return form


class StockLocationCreate(AjaxCreateView):
    """
    View for creating a new StockLocation
    A parent location (another StockLocation object) can be passed as a query parameter
    """

    model = StockLocation
    form_class = EditStockLocationForm
    context_object_name = 'location'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create new Stock Location'

    def get_initial(self):
        initials = super(StockLocationCreate, self).get_initial().copy()

        loc_id = self.request.GET.get('location', None)

        if loc_id:
            try:
                initials['parent'] = StockLocation.objects.get(pk=loc_id)
            except StockLocation.DoesNotExist:
                pass

        return initials


class StockItemCreate(AjaxCreateView):
    """
    View for creating a new StockItem
    Parameters can be pre-filled by passing query items:
    - part: The part of which the new StockItem is an instance
    - location: The location of the new StockItem
    """

    model = StockItem
    form_class = CreateStockItemForm
    context_object_name = 'item'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create new Stock Item'

    def get_form(self):
        """ Get form for StockItem creation.
        Overrides the default get_form() method to intelligently limit
        ForeignKey choices based on other selections
        """

        form = super(AjaxCreateView, self).get_form()

        # If the user has selected a Part, limit choices for SupplierPart
        if form['part'].value():
            part_id = form['part'].value()

            try:
                part = Part.objects.get(id=part_id)
                parts = form.fields['supplier_part'].queryset
                parts = parts.filter(part=part.id)

                # If the part is NOT purchaseable, hide the supplier_part field
                if not part.purchaseable:
                    form.fields['supplier_part'].widget = HiddenInput()

                form.fields['supplier_part'].queryset = parts

                # If there is one (and only one) supplier part available, pre-select it
                all_parts = parts.all()
                if len(all_parts) == 1:

                    # TODO - This does NOT work for some reason? Ref build.views.BuildItemCreate
                    form.fields['supplier_part'].initial = all_parts[0].id

            except Part.DoesNotExist:
                pass

            # Hide the 'part' field
            form.fields['part'].widget = HiddenInput()

        # Otherwise if the user has selected a SupplierPart, we know what Part they meant!
        elif form['supplier_part'].value() is not None:
            pass

        return form

    def get_initial(self):
        """ Provide initial data to create a new StockItem object
        """

        # Is the client attempting to copy an existing stock item?
        item_to_copy = self.request.GET.get('copy', None)

        if item_to_copy:
            try:
                original = StockItem.objects.get(pk=item_to_copy)
                initials = model_to_dict(original)
                self.ajax_form_title = "Copy Stock Item"
            except StockItem.DoesNotExist:
                initials = super(StockItemCreate, self).get_initial().copy()

        else:
            initials = super(StockItemCreate, self).get_initial().copy()

        part_id = self.request.GET.get('part', None)
        loc_id = self.request.GET.get('location', None)

        # Part field has been specified
        if part_id:
            try:
                part = Part.objects.get(pk=part_id)
                initials['part'] = part
                initials['location'] = part.get_default_location()
                initials['supplier_part'] = part.default_supplier
            except Part.DoesNotExist:
                pass

        # Location has been specified
        if loc_id:
            try:
                initials['location'] = StockLocation.objects.get(pk=loc_id)
            except StockLocation.DoesNotExist:
                pass

        return initials


class StockLocationDelete(AjaxDeleteView):
    """
    View to delete a StockLocation
    Presents a deletion confirmation form to the user
    """

    model = StockLocation
    success_url = '/stock'
    ajax_template_name = 'stock/location_delete.html'
    context_object_name = 'location'
    ajax_form_title = 'Delete Stock Location'


class StockItemDelete(AjaxDeleteView):
    """
    View to delete a StockItem
    Presents a deletion confirmation form to the user
    """

    model = StockItem
    success_url = '/stock/'
    ajax_template_name = 'stock/item_delete.html'
    context_object_name = 'item'
    ajax_form_title = 'Delete Stock Item'


class StockItemMove(AjaxUpdateView):
    """
    View to move a StockItem from one location to another
    Performs some data validation to prevent illogical stock moves
    """

    model = StockItem
    ajax_template_name = 'modal_form.html'
    context_object_name = 'item'
    ajax_form_title = 'Move Stock Item'
    form_class = MoveStockItemForm

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, instance=self.get_object())

        if form.is_valid():

            obj = self.get_object()

            try:
                loc_id = form['location'].value()

                if loc_id:
                    loc = StockLocation.objects.get(pk=form['location'].value())
                    if str(loc.pk) == str(obj.pk):
                        form.errors['location'] = ['Item is already in this location']
                    else:
                        obj.move(loc, form['note'].value(), request.user)
                else:
                    form.errors['location'] = ['Cannot move to an empty location']

            except StockLocation.DoesNotExist:
                form.errors['location'] = ['Location does not exist']

        data = {
            'form_valid': form.is_valid() and len(form.errors) == 0,
        }

        return self.renderJsonResponse(request, form, data)


class StockItemStocktake(AjaxUpdateView):
    """
    View to perform stocktake on a single StockItem
    Updates the quantity, which will also create a new StockItemTracking item
    """

    model = StockItem
    template_name = 'modal_form.html'
    context_object_name = 'item'
    ajax_form_title = 'Item stocktake'
    form_class = StocktakeForm

    def post(self, request, *args, **kwargs):

        form = self.form_class(request.POST, instance=self.get_object())

        if form.is_valid():

            obj = self.get_object()

            obj.stocktake(form.data['quantity'], request.user)

        data = {
            'form_valid': form.is_valid()
        }

        return self.renderJsonResponse(request, form, data)


class StockTrackingIndex(ListView):
    """
    StockTrackingIndex provides a page to display StockItemTracking objects
    """

    model = StockItemTracking
    template_name = 'stock/tracking.html'
    context_object_name = 'items'
