# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin
from import_export.resources import ModelResource
from import_export.fields import Field
import import_export.widgets as widgets

from .models import StockLocation, StockItem, StockItemAttachment
from .models import StockItemTracking
from .models import StockItemTestResult

from build.models import Build
from company.models import SupplierPart
from order.models import PurchaseOrder, SalesOrder
from part.models import Part


class LocationResource(ModelResource):
    """ Class for managing StockLocation data import/export """

    parent = Field(attribute='parent', widget=widgets.ForeignKeyWidget(StockLocation))

    parent_name = Field(attribute='parent__name', readonly=True)

    class Meta:
        model = StockLocation
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

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

    search_fields = ('name', 'description')


class StockItemResource(ModelResource):
    """ Class for managing StockItem data import/export """

    # Custom manaegrs for ForeignKey fields
    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(Part))

    part_name = Field(attribute='part__full_ame', readonly=True)

    supplier_part = Field(attribute='supplier_part', widget=widgets.ForeignKeyWidget(SupplierPart))

    supplier = Field(attribute='supplier_part__supplier__id', readonly=True)

    supplier_name = Field(attribute='supplier_part__supplier__name', readonly=True)

    status_label = Field(attribute='status_label', readonly=True)

    location = Field(attribute='location', widget=widgets.ForeignKeyWidget(StockLocation))

    location_name = Field(attribute='location__name', readonly=True)

    belongs_to = Field(attribute='belongs_to', widget=widgets.ForeignKeyWidget(StockItem))

    build = Field(attribute='build', widget=widgets.ForeignKeyWidget(Build))

    sales_order = Field(attribute='sales_order', widget=widgets.ForeignKeyWidget(SalesOrder))

    build_order = Field(attribute='build_order', widget=widgets.ForeignKeyWidget(Build))

    purchase_order = Field(attribute='purchase_order', widget=widgets.ForeignKeyWidget(PurchaseOrder))

    # Date management
    updated = Field(attribute='updated', widget=widgets.DateWidget())
    
    stocktake_date = Field(attribute='stocktake_date', widget=widgets.DateWidget())

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):

        super().after_import(dataset, result, using_transactions, dry_run, **kwargs)

        # Rebuild the StockItem tree(s)
        StockItem.objects.rebuild()

    class Meta:
        model = StockItem
        skip_unchanged = True
        report_skipped = False
        clean_model_instance = True


class StockItemAdmin(ImportExportModelAdmin):

    resource_class = StockItemResource

    list_display = ('part', 'quantity', 'location', 'status', 'updated')


class StockAttachmentAdmin(admin.ModelAdmin):

    list_display = ('stock_item', 'attachment', 'comment')
    

class StockTrackingAdmin(ImportExportModelAdmin):
    list_display = ('item', 'date', 'title')


class StockItemTestResultAdmin(admin.ModelAdmin):

    list_display = ('stock_item', 'test', 'result', 'value')


admin.site.register(StockLocation, LocationAdmin)
admin.site.register(StockItem, StockItemAdmin)
admin.site.register(StockItemTracking, StockTrackingAdmin)
admin.site.register(StockItemAttachment, StockAttachmentAdmin)
admin.site.register(StockItemTestResult, StockItemTestResultAdmin)
