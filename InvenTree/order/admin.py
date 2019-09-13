# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import PurchaseOrder, PurchaseOrderLineItem


class PurchaseOrderAdmin(ImportExportModelAdmin):

    list_display = (
        'reference',
        'supplier',
        'status',
        'description',
        'creation_date'
    )


class PurchaseOrderLineItemAdmin(ImportExportModelAdmin):

    list_display = (
        'order',
        'part',
        'quantity',
        'reference'
    )


admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(PurchaseOrderLineItem, PurchaseOrderLineItemAdmin)
