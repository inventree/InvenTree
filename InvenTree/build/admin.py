# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Build, BuildItem


class BuildAdmin(ImportExportModelAdmin):

    list_display = (
        'part',
        'status',
        'batch',
        'quantity',
        'creation_date',
        'completion_date',
        'title',
        'notes',
    )


class BuildItemAdmin(admin.ModelAdmin):

    list_display = (
        'build',
        'stock_item',
        'quantity'
    )


admin.site.register(Build, BuildAdmin)
admin.site.register(BuildItem, BuildItemAdmin)
