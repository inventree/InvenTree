# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin
from import_export.resources import ModelResource
from import_export.fields import Field
import import_export.widgets as widgets

from .models import Company
from .models import SupplierPart
from .models import SupplierPriceBreak

from part.models import Part


class CompanyResource(ModelResource):
    """ Class for managing Company data import/export """

    class Meta:
        model = Company
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True


class CompanyAdmin(ImportExportModelAdmin):

    resource_class = CompanyResource

    list_display = ('name', 'website', 'contact')

    search_fields = [
        'name',
        'description',
    ]


class SupplierPartResource(ModelResource):
    """
    Class for managing SupplierPart data import/export
    """

    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(Part))

    part_name = Field(attribute='part__full_name', readonly=True)

    supplier = Field(attribute='supplier', widget=widgets.ForeignKeyWidget(Company))

    supplier_name = Field(attribute='supplier__name', readonly=True)

    class Meta:
        model = SupplierPart
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True


class SupplierPartAdmin(ImportExportModelAdmin):

    resource_class = SupplierPartResource

    list_display = ('part', 'supplier', 'SKU')

    search_fields = [
        'company__name',
        'part__name',
        'MPN',
        'SKU',
    ]


class SupplierPriceBreakResource(ModelResource):
    """ Class for managing SupplierPriceBreak data import/export """

    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(SupplierPart))

    supplier_id = Field(attribute='part__supplier__pk', readonly=True)

    supplier_name = Field(attribute='part__supplier__name', readonly=True)

    part_name = Field(attribute='part__part__full_name', readonly=True)

    SKU = Field(attribute='part__SKU', readonly=True)

    MPN = Field(attribute='part__MPN', readonly=True)

    class Meta:
        model = SupplierPriceBreak
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True


class SupplierPriceBreakAdmin(ImportExportModelAdmin):

    resource_class = SupplierPriceBreakResource

    list_display = ('part', 'quantity', 'price')


admin.site.register(Company, CompanyAdmin)
admin.site.register(SupplierPart, SupplierPartAdmin)
admin.site.register(SupplierPriceBreak, SupplierPriceBreakAdmin)
