from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from .models import Supplier, SupplierPart

class SupplierIndex(ListView):
    model = Supplier
    template_name = 'supplier/index.html'
    context_object_name = 'suppliers'
    paginate_by = 50

    def get_queryset(self):
        return Supplier.objects.order_by('name')


class SupplierDetail(DetailView):
    context_obect = 'supplier'
    template_name = 'supplier/detail.html'
    queryset = Supplier.objects.all()


def partDetail(request, pk):
    """ The supplier part-detail page shows detailed information
    on a particular supplier part
    """

    part = get_object_or_404(SupplierPart, pk=pk)

    return render(request, 'supplier/partdetail.html', {'part': part})