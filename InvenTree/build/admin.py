# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from import_export.resources import ModelResource
import import_export.widgets as widgets

from build.models import Build, BuildItem

import part.models


class BuildResource(ModelResource):
    """Class for managing import/export of Build data"""
    # For some reason, we need to specify the fields individually for this ModelResource,
    # but we don't for other ones. 
    # TODO: 2022-05-12 - Need to investigate why this is the case!

    pk = Field(attribute='pk')

    reference = Field(attribute='reference')

    title = Field(attribute='title')

    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(part.models.Part))

    part_name = Field(attribute='part__full_name', readonly=True)

    overdue = Field(attribute='is_overdue', readonly=True, widget=widgets.BooleanWidget())

    completed = Field(attribute='completed', readonly=True)

    quantity = Field(attribute='quantity')

    status = Field(attribute='status')

    batch = Field(attribute='batch')

    notes = Field(attribute='notes')

    class Meta:
        models = Build
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True
        exclude = [
            'lft', 'rght', 'tree_id', 'level',
        ]



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
