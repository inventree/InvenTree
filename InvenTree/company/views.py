from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from part.models import Part
from .models import Company
from .models import SupplierPart
from .models import SupplierOrder

from .forms import EditCompanyForm
from .forms import EditSupplierPartForm
from .forms import EditSupplierOrderForm

class SupplierOrderDetail(DetailView):
    context_object_name = 'order'
    model = SupplierOrder
    template_name = 'company/order_detail.html'
    queryset = SupplierOrder.objects.all()


class SupplierOrderCreate(CreateView):
    model = SupplierOrder
    form_class = EditSupplierOrderForm
    context_object_name = 'supplier'
    template_name = 'company/order_create.html'

    def get_initial(self):
        initials = super(SupplierOrderCreate, self).get_initial().copy()

        s_id = self.request.GET.get('supplier', None)

        if s_id:
            initials['supplier'] = get_object_or_404(Supplier, pk=s_id)

        return initials


class CompanyIndex(ListView):
    model = Company
    template_name = 'company/index.html'
    context_object_name = 'companies'
    paginate_by = 50

    def get_queryset(self):
        return Supplier.objects.order_by('name')


class CompanyDetail(DetailView):
    context_obect_name = 'company'
    template_name = 'company/detail.html'
    queryset = Company.objects.all()
    model = Company


class CompanyEdit(UpdateView):
    model = Company
    form_class = EditCompanyForm
    template_name = 'company/edit.html'
    context_object_name = 'supplier'


class CompanyCreate(CreateView):
    model = Company
    form_class = EditCompanyForm
    template_name = "company/create.html"


class CompanyDelete(DeleteView):
    model = Company
    success_url = '/company/'
    template_name = 'company/delete.html'

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(CompanyDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())


class SupplierPartDetail(DetailView):
    model = SupplierPart
    template_name = 'company/partdetail.html'
    context_object_name = 'part'
    queryset = SupplierPart.objects.all()


class SupplierPartEdit(UpdateView):
    model = SupplierPart
    template_name = 'company/partedit.html'
    context_object_name = 'part'
    form_class = EditSupplierPartForm


class SupplierPartCreate(CreateView):
    model = SupplierPart
    form_class = EditSupplierPartForm
    template_name = 'company/partcreate.html'
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
    template_name = 'company/partdelete.html'

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(SupplierPartDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())
