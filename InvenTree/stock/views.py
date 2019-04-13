# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404

from django.views.generic import DetailView, ListView

from InvenTree.views import AjaxUpdateView, AjaxDeleteView, AjaxCreateView

from part.models import Part
from .models import StockItem, StockLocation

from .forms import EditStockLocationForm
from .forms import CreateStockItemForm
from .forms import EditStockItemForm
from .forms import MoveStockItemForm
from .forms import StocktakeForm


class StockIndex(ListView):
    """
    StockIndex view loads all StockLocation and StockItem object
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
    template_name = 'stock/location_edit.html'
    context_object_name = 'location'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Stock Location'


class StockItemEdit(AjaxUpdateView):
    """
    View for editing details of a single StockItem
    """

    model = StockItem
    form_class = EditStockItemForm
    template_name = 'stock/item_edit.html'
    context_object_name = 'item'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Stock Item'


class StockLocationCreate(AjaxCreateView):
    """
    View for creating a new StockLocation
    A parent location (another StockLocation object) can be passed as a query parameter
    """

    model = StockLocation
    form_class = EditStockLocationForm
    template_name = 'stock/location_create.html'
    context_object_name = 'location'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create new Stock Location'

    def get_initial(self):
        initials = super(StockLocationCreate, self).get_initial().copy()

        loc_id = self.request.GET.get('location', None)

        if loc_id:
            initials['parent'] = get_object_or_404(StockLocation, pk=loc_id)

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
    template_name = 'stock/item_create.html'
    context_object_name = 'item'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create new Stock Item'

    def get_initial(self):
        initials = super(StockItemCreate, self).get_initial().copy()

        part_id = self.request.GET.get('part', None)
        loc_id = self.request.GET.get('location', None)

        if part_id:
            part = get_object_or_404(Part, pk=part_id)
            if part:
                initials['part'] = get_object_or_404(Part, pk=part_id)
                initials['location'] = part.default_location
                initials['supplier_part'] = part.default_supplier

        if loc_id:
            initials['location'] = get_object_or_404(StockLocation, pk=loc_id)

        return initials


class StockLocationDelete(AjaxDeleteView):
    """
    View to delete a StockLocation
    Presents a deletion confirmation form to the user
    """

    model = StockLocation
    success_url = '/stock'
    template_name = 'stock/location_delete.html'
    context_object_name = 'location'
    ajax_form_title = 'Delete Stock Location'


class StockItemDelete(AjaxDeleteView):
    """
    View to delete a StockItem
    Presents a deletion confirmation form to the user
    """

    model = StockItem
    success_url = '/stock/'
    template_name = 'stock/item_delete.html'
    context_object_name = 'item'
    ajax_form_title = 'Delete Stock Item'


class StockItemMove(AjaxUpdateView):
    """
    View to move a StockItem from one location to another
    Performs some data validation to prevent illogical stock moves
    """

    model = StockItem
    template_name = 'modal_form.html'
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
