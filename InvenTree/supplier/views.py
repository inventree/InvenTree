from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from part.models import Part
from .models import Supplier, SupplierPart

from .forms import EditSupplierForm
from .forms import EditSupplierPartForm

class SupplierIndex(ListView):
    model = Supplier
    template_name = 'supplier/index.html'
    context_object_name = 'suppliers'
    paginate_by = 50

    def get_queryset(self):
        return Supplier.objects.order_by('name')


class SupplierDetail(DetailView):
    context_obect_name = 'supplier'
    template_name = 'supplier/detail.html'
    queryset = Supplier.objects.all()
    model = Supplier


class SupplierEdit(UpdateView):
    model = Supplier
    form_class = EditSupplierForm
    template_name = 'supplier/edit.html'
    context_object_name = 'supplier'


class SupplierCreate(CreateView):
    model = Supplier
    form_class = EditSupplierForm
    template_name = "supplier/create.html"


class SupplierDelete(DeleteView):
    model = Supplier
    success_url = '/supplier/'
    template_name = 'supplier/delete.html'

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(SupplierDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())


class SupplierPartDetail(DetailView):
    model = SupplierPart
    template_name = 'supplier/partdetail.html'
    context_object_name = 'part'
    queryset = SupplierPart.objects.all()


class SupplierPartEdit(UpdateView):
    model = SupplierPart
    template_name = 'supplier/partedit.html'
    context_object_name = 'part'
    form_class = EditSupplierPartForm


class SupplierPartCreate(CreateView):
    model = SupplierPart
    form_class = EditSupplierPartForm
    template_name = 'supplier/partcreate.html'
    context_object_name = 'part'

    def get_initial(self):
        initials = super(SupplierPartCreate, self).get_initial().copy()

        supplier_id = self.request.GET.get('supplier', None)
        part_id = self.request.GET.get('part', None)

        if supplier_id:
            initials['supplier'] = get_object_or_404(Supplier, pk=supplier_id)
            # TODO
            # self.fields['supplier'].disabled = True
        if part_id:
            initials['part'] = get_object_or_404(Part, pk=part_id)
            # TODO
            # self.fields['part'].disabled = True

        return initials


class SupplierPartDelete(DeleteView):
    model = SupplierPart
    success_url = '/supplier/'
    template_name = 'supplier/partdelete.html'

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(SupplierPartDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())
