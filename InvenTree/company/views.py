# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponseRedirect

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from .models import Company

from .forms import EditCompanyForm


class CompanyIndex(ListView):
    model = Company
    template_name = 'company/index.html'
    context_object_name = 'companies'
    paginate_by = 50

    def get_queryset(self):
        queryset = Company.objects.all().order_by('name')

        if self.request.GET.get('supplier', None):
            queryset = queryset.filter(is_supplier=True)

        if self.request.GET.get('customer', None):
            queryset = queryset.filter(is_customer=True)

        return queryset


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
