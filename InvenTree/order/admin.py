# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderLineItem


class PurchaseOrderAdmin(admin.ModelAdmin):

    list_display = (
        'reference',
        'supplier',
        'status',
        'description',
        'creation_date'
    )


class PurchaseOrderLineItemAdmin(admin.ModelAdmin):

    list_display = (
        'order',
        'part',
        'quantity',
        'reference'
    )


admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(PurchaseOrderLineItem, PurchaseOrderLineItemAdmin)
