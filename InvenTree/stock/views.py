from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from InvenTree.views import AjaxUpdateView, AjaxDeleteView, AjaxCreateView

from part.models import Part
from .models import StockItem, StockLocation

from .forms import EditStockLocationForm
from .forms import EditStockItemForm


class StockIndex(ListView):
    model = StockItem
    template_name = 'stock/index.html'
    context_obect_name = 'locations'

    def get_context_data(self, **kwargs):
        context = super(StockIndex, self).get_context_data(**kwargs).copy()

        # Return all top-level locations
        locations = StockLocation.objects.filter(parent=None)

        context['locations'] = locations
        context['items'] = StockItem.objects.all()

        return context


class StockLocationDetail(DetailView):
    context_object_name = 'location'
    template_name = 'stock/location.html'
    queryset = StockLocation.objects.all()
    model = StockLocation


class StockItemDetail(DetailView):
    context_object_name = 'item'
    template_name = 'stock/item.html'
    queryset = StockItem.objects.all()
    model = StockItem


class StockLocationEdit(AjaxUpdateView):
    model = StockLocation
    form_class = EditStockLocationForm
    template_name = 'stock/location_edit.html'
    context_object_name = 'location'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Stock Location'


class StockItemEdit(AjaxUpdateView):
    model = StockItem
    form_class = EditStockItemForm
    template_name = 'stock/item_edit.html'
    context_object_name = 'item'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Stock Item'


class StockLocationCreate(AjaxCreateView):
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
    model = StockItem
    form_class = EditStockItemForm
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
    model = StockLocation
    success_url = '/stock'
    template_name = 'stock/location_delete.html'
    context_object_name = 'location'
    ajax_form_title = 'Delete Stock Location'


class StockItemDelete(AjaxDeleteView):
    model = StockItem
    success_url = '/stock/'
    template_name = 'stock/item_delete.html'
    context_object_name = 'item'
    ajax_form_title = 'Delete Stock Item'
