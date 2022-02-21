# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Build, BuildItem


class BuildAdmin(ImportExportModelAdmin):

    exclude = [
        'reference_int',
    ]

    list_display = (
        'reference',
        'title',
        'part',
        'status',
        'batch',
        'quantity',
    )

    search_fields = [
        'reference',
        'title',
        'part__name',
        'part__description',
    ]

    autocomplete_fields = [
        'parent',
        'part',
        'sales_order',
        'take_from',
        'destination',
    ]


class BuildItemAdmin(admin.ModelAdmin):

    list_display = (
        'build',
        'stock_item',
        'quantity'
    )

    autocomplete_fields = [
        'build',
        'bom_item',
        'stock_item',
        'install_into',
    ]


admin.site.register(Build, BuildAdmin)
admin.site.register(BuildItem, BuildItemAdmin)
