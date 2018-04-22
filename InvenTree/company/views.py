from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from part.models import Part
from .models import Company
#from .models import SupplierOrder

from .forms import EditCompanyForm
#from .forms import EditSupplierOrderForm

"""
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
"""


class CompanyIndex(ListView):
    model = Company
    template_name = 'company/index.html'
    context_object_name = 'companies'
    paginate_by = 50

    def get_queryset(self):
        return Company.objects.order_by('name')


class CompanyDetail(DetailView):
    context_obect_name = 'company'
    template_name = 'company/detail.html'
    queryset = Company.objects.all()
    model = Company


class CompanyEdit(UpdateView):
    model = Company
    form_class = EditCompanyForm
    template_name = 'company/edit.html'
    context_object_name = 'company'


class CompanyCreate(CreateView):
    model = Company
    context_object_name = 'company'
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


