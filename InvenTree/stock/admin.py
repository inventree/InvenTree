# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin
from import_export.resources import ModelResource
from import_export.fields import Field
import import_export.widgets as widgets

from .models import StockLocation, StockItem
from .models import StockItemTracking


class LocationResource(ModelResource):
    """ Class for managing StockLocation data import/export """

    parent = Field(attribute='parent', widget=widgets.ForeignKeyWidget(StockLocation))

    parent_name = Field(attribute='parent__name', readonly=True)

    class Meta:
        model = StockLocation
        skip_unchanged = True
        report_skipped = False

        exclude = [
            # Exclude MPTT internal model fields
            'lft', 'rght', 'tree_id', 'level',
        ]

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):

        super().after_import(dataset, result, using_transactions, dry_run, **kwargs)

        # Rebuild the StockLocation tree(s)
        StockLocation.objects.rebuild()


class LocationAdmin(ImportExportModelAdmin):

    resource_class = LocationResource

    list_display = ('name', 'pathstring', 'description')


class StockItemAdmin(ImportExportModelAdmin):
    list_display = ('part', 'quantity', 'location', 'status', 'updated')


class StockTrackingAdmin(ImportExportModelAdmin):
    list_display = ('item', 'date', 'title')


admin.site.register(StockLocation, LocationAdmin)
admin.site.register(StockItem, StockItemAdmin)
admin.site.register(StockItemTracking, StockTrackingAdmin)
