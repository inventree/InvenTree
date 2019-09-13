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
from common.models import Currency


class CompanyResource(ModelResource):
    """ Class for managing Company data import/export """

    class Meta:
        model = Company
        skip_unchanged = True
        report_skipped = False


class CompanyAdmin(ImportExportModelAdmin):

    resource_class = CompanyResource

    list_display = ('name', 'website', 'contact')


class SupplierPartResource(ModelResource):
    """ Class for managing SupplierPart data import/export """

    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(Part))

    supplier = Field(attribute='supplier', widget=widgets.ForeignKeyWidget(Company))

    class Meta:
        model = SupplierPart
        skip_unchanged = True
        report_skipped = False


class SupplierPartAdmin(ImportExportModelAdmin):

    resource_class = SupplierPartResource

    list_display = ('part', 'supplier', 'SKU')


class SupplierPriceBreakResource(ModelResource):
    """ Class for managing SupplierPriceBreak data import/export """

    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(SupplierPart))

    currency = Field(attribute='currency', widget=widgets.ForeignKeyWidget(Currency))

    class Meta:
        model = SupplierPriceBreak
        skip_unchanged = True
        report_skipped = False


class SupplierPriceBreakAdmin(ImportExportModelAdmin):

    resource_class = SupplierPriceBreakResource

    list_display = ('part', 'quantity', 'cost')


admin.site.register(Company, CompanyAdmin)
admin.site.register(SupplierPart, SupplierPartAdmin)
admin.site.register(SupplierPriceBreak, SupplierPriceBreakAdmin)
