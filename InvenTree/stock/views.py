from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView


from .models import StockItem, StockLocation

from .forms import EditStockLocationForm
from .forms import EditStockItemForm

class StockIndex(ListView):
    model = StockItem
    template_name = 'stock/index.html'
    context_obect_name = 'items'
    paginate_by = 50

    def get_queryset(self):
        return StockItem.objects.filter(location=None)

    def get_context_data(self, **kwargs):
        context = super(StockIndex, self).get_context_data(**kwargs).copy()

        locations = StockLocation.objects.filter(parent=None)

        context['locations'] = locations

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


class StockLocationEdit(UpdateView):
    model = StockLocation
    form_class = EditStockLocationForm
    template_name = '/stock/location-edit.html'
    context_object_name = 'location'


class StockItemEdit(UpdateView):
    model = StockItem
    form_class = EditStockItemForm
    template_name = '/stock/item-edit.html'
    context_object_name = 'item'


class StockLocationCreate(CreateView):
    model = StockLocation
    form_class = EditStockLocationForm
    template_name = '/stock/location-create.html'
    context_object_name = 'location'


class StockItemCreate(CreateView):
    model = StockItem
    form_class = EditStockItemForm
    template_name = '/stock/item-create.html'
    context_object_name = 'item'


class StockLocationDelete(DeleteView):
    model = StockLocation
    success_url = '/stock/'
    template_name = '/stock/location-delete.html'

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(StockLocationDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())


class StockItemDelete(DeleteView):
    model = StockLocation
    success_url = '/stock/'
    template_name = '/stock/item-delete.html'

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(StockItemDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())