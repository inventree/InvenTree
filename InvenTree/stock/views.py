from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from part.models import Part
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
    template_name = 'stock/location_edit.html'
    context_object_name = 'location'


class StockItemEdit(UpdateView):
    model = StockItem
    form_class = EditStockItemForm
    template_name = 'stock/item_edit.html'
    context_object_name = 'item'


class StockLocationCreate(CreateView):
    model = StockLocation
    form_class = EditStockLocationForm
    template_name = 'stock/location_create.html'
    context_object_name = 'location'

    def get_initial(self):
        initials = super(StockLocationCreate, self).get_initial().copy()

        loc_id = self.request.GET.get('location', None)

        if loc_id:
            initials['parent'] = get_object_or_404(StockLocation, pk=loc_id)

        return initials


class StockItemCreate(CreateView):
    model = StockItem
    form_class = EditStockItemForm
    template_name = 'stock/item_create.html'
    context_object_name = 'item'

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


class StockLocationDelete(DeleteView):
    model = StockLocation
    success_url = '/stock'
    template_name = 'stock/location_delete.html'
    context_object_name = 'location'

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(StockLocationDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())


class StockItemDelete(DeleteView):
    model = StockItem
    success_url = '/stock/'
    template_name = 'stock/item_delete.html'
    context_object_name = 'item'

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(StockItemDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())
