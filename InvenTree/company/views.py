# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import DetailView, ListView

from InvenTree.views import AjaxCreateView, AjaxUpdateView, AjaxDeleteView

from .models import Company

from .forms import EditCompanyForm
from .forms import CompanyImageForm


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


class CompanyImage(AjaxUpdateView):
    model = Company
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Update Company Image'
    form_class = CompanyImageForm

    def get_data(self):
        return {
            'success': 'Updated company image',
        }


class CompanyEdit(AjaxUpdateView):
    model = Company
    form_class = EditCompanyForm
    template_name = 'company/edit.html'
    context_object_name = 'company'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Company'

    def get_data(self):
        return {
            'info': 'Edited company information',
        }


class CompanyCreate(AjaxCreateView):
    model = Company
    context_object_name = 'company'
    form_class = EditCompanyForm
    template_name = "company/create.html"
    ajax_template_name = 'modal_form.html'
    ajax_form_title = "Create new Company"

    def get_data(self):
        return {
            'success': "Created new company",
        }


class CompanyDelete(AjaxDeleteView):
    model = Company
    success_url = '/company/'
    template_name = 'company/delete.html'
    ajax_form_title = 'Delete Company'

    def get_data(self):
        return {
            'danger': 'Company was deleted',
        }
