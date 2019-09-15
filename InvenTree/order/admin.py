# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin

from import_export.resources import ModelResource
from import_export.fields import Field

from .models import PurchaseOrder, PurchaseOrderLineItem


class PurchaseOrderAdmin(ImportExportModelAdmin):

    list_display = (
        'reference',
        'supplier',
        'status',
        'description',
        'creation_date'
    )


class POLineItemResource(ModelResource):
    """ Class for managing import / export of POLineItem data """

    part_name = Field(attribute='part__part__name', readonly=True)

    manufacturer = Field(attribute='part__manufacturer', readonly=True)

    MPN = Field(attribute='part__MPN', readonly=True)

    SKU = Field(attribute='part__SKU', readonly=True)

    class Meta:
        model = PurchaseOrderLineItem
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True


class PurchaseOrderLineItemAdmin(ImportExportModelAdmin):

    resource_class = POLineItemResource

    list_display = (
        'order',
        'part',
        'quantity',
        'reference'
    )


admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(PurchaseOrderLineItem, PurchaseOrderLineItemAdmin)
