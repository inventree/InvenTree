"""
Django views for interacting with Company app
"""


# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import DetailView, ListView

from InvenTree.views import AjaxCreateView, AjaxUpdateView, AjaxDeleteView

from .models import Company

from .forms import EditCompanyForm
from .forms import CompanyImageForm


class CompanyIndex(ListView):
    """ View for displaying list of companies 
    """

    model = Company
    template_name = 'company/index.html'
    context_object_name = 'companies'
    paginate_by = 50

    def get_queryset(self):
        """ Retrieve the Company queryset based on HTTP request parameters.

        - supplier: Filter by supplier
        - customer: Filter by customer
        """
        queryset = Company.objects.all().order_by('name')

        if self.request.GET.get('supplier', None):
            queryset = queryset.filter(is_supplier=True)

        if self.request.GET.get('customer', None):
            queryset = queryset.filter(is_customer=True)

        return queryset


class CompanyDetail(DetailView):
    """ Detail view for Company object """
    context_obect_name = 'company'
    template_name = 'company/detail.html'
    queryset = Company.objects.all()
    model = Company


class CompanyImage(AjaxUpdateView):
    """ View for uploading an image for the Company """
    model = Company
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Update Company Image'
    form_class = CompanyImageForm

    def get_data(self):
        return {
            'success': 'Updated company image',
        }


class CompanyEdit(AjaxUpdateView):
    """ View for editing a Company object """
    model = Company
    form_class = EditCompanyForm
    context_object_name = 'company'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Company'

    def get_data(self):
        return {
            'info': 'Edited company information',
        }


class CompanyCreate(AjaxCreateView):
    """ View for creating a new Company object """
    model = Company
    context_object_name = 'company'
    form_class = EditCompanyForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = "Create new Company"

    def get_data(self):
        return {
            'success': "Created new company",
        }


class CompanyDelete(AjaxDeleteView):
    """ View for deleting a Company object """
    model = Company
    success_url = '/company/'
    ajax_template_name = 'company/delete.html'
    ajax_form_title = 'Delete Company'

    def get_data(self):
        return {
            'danger': 'Company was deleted',
        }
