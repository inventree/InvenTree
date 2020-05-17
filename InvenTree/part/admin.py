# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin
from import_export.resources import ModelResource
from import_export.fields import Field
import import_export.widgets as widgets

from .models import PartCategory, Part
from .models import PartAttachment, PartStar
from .models import BomItem
from .models import PartParameterTemplate, PartParameter
from .models import PartTestTemplate

from stock.models import StockLocation
from company.models import SupplierPart


class PartResource(ModelResource):
    """ Class for managing Part data import/export """

    # ForeignKey fields
    category = Field(attribute='category', widget=widgets.ForeignKeyWidget(PartCategory))
    
    default_location = Field(attribute='default_location', widget=widgets.ForeignKeyWidget(StockLocation))

    default_supplier = Field(attribute='default_supplier', widget=widgets.ForeignKeyWidget(SupplierPart))

    category_name = Field(attribute='category__name', readonly=True)
    
    variant_of = Field(attribute='variant_of', widget=widgets.ForeignKeyWidget(Part))

    suppliers = Field(attribute='supplier_count', readonly=True)

    # Extra calculated meta-data (readonly)
    in_stock = Field(attribute='total_stock', readonly=True, widget=widgets.IntegerWidget())

    on_order = Field(attribute='on_order', readonly=True, widget=widgets.IntegerWidget())

    used_in = Field(attribute='used_in_count', readonly=True, widget=widgets.IntegerWidget())

    allocated = Field(attribute='allocation_count', readonly=True, widget=widgets.IntegerWidget())

    building = Field(attribute='quantity_being_built', readonly=True, widget=widgets.IntegerWidget())

    class Meta:
        model = Part
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True
        exclude = [
            'bom_checksum', 'bom_checked_by', 'bom_checked_date'
        ]

    def get_queryset(self):
        """ Prefetch related data for quicker access """

        query = super().get_queryset()
        query = query.prefetch_related(
            'category',
            'used_in',
            'builds',
            'supplier_parts__purchase_order_line_items',
            'stock_items__allocations'
        )

        return query


class PartAdmin(ImportExportModelAdmin):
    
    resource_class = PartResource

    list_display = ('full_name', 'description', 'total_stock', 'category')

    list_filter = ('active', 'assembly', 'is_template', 'virtual')

    search_fields = ('name', 'description', 'category__name', 'category__description', 'IPN')


class PartCategoryResource(ModelResource):
    """ Class for managing PartCategory data import/export """

    parent = Field(attribute='parent', widget=widgets.ForeignKeyWidget(PartCategory))

    parent_name = Field(attribute='parent__name', readonly=True)

    default_location = Field(attribute='default_location', widget=widgets.ForeignKeyWidget(StockLocation))

    class Meta:
        model = PartCategory
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

        exclude = [
            # Exclude MPTT internal model fields
            'lft', 'rght', 'tree_id', 'level',
        ]

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):

        super().after_import(dataset, result, using_transactions, dry_run, **kwargs)

        # Rebuild the PartCategory tree(s)
        PartCategory.objects.rebuild()


class PartCategoryAdmin(ImportExportModelAdmin):

    resource_class = PartCategoryResource

    list_display = ('name', 'pathstring', 'description')

    search_fields = ('name', 'description')


class PartAttachmentAdmin(admin.ModelAdmin):

    list_display = ('part', 'attachment', 'comment')


class PartStarAdmin(admin.ModelAdmin):

    list_display = ('part', 'user')


class PartTestTemplateAdmin(admin.ModelAdmin):

    list_display = ('part', 'test_name', 'required')


class BomItemResource(ModelResource):
    """ Class for managing BomItem data import/export """

    level = Field(attribute='level', readonly=True)

    bom_id = Field(attribute='pk')

    parent_part_id = Field(attribute='part', widget=widgets.ForeignKeyWidget(Part))

    parent_part_name = Field(attribute='part__full_name', readonly=True)

    sub_part_id = Field(attribute='sub_part', widget=widgets.ForeignKeyWidget(Part))

    sub_part_name = Field(attribute='sub_part__full_name', readonly=True)

    sub_assembly = Field(attribute='sub_part__assembly', readonly=True)

    class Meta:
        model = BomItem
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

        exclude = [
            'checksum',
            'id',
            'part',
            'sub_part',
        ]


class BomItemAdmin(ImportExportModelAdmin):

    resource_class = BomItemResource

    list_display = ('part', 'sub_part', 'quantity')

    search_fields = ('part__name', 'part__description', 'sub_part__name', 'sub_part__description')


class ParameterTemplateAdmin(ImportExportModelAdmin):
    list_display = ('name', 'units')


class ParameterResource(ModelResource):
    """ Class for managing PartParameter data import/export """

    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(Part))

    part_name = Field(attribute='part__name', readonly=True)

    template = Field(attribute='template', widget=widgets.ForeignKeyWidget(PartParameterTemplate))

    template_name = Field(attribute='template__name', readonly=True)

    class Meta:
        model = PartParameter
        skip_unchanged = True
        report_skipped = False
        clean_model_instance = True


class ParameterAdmin(ImportExportModelAdmin):

    resource_class = ParameterResource

    list_display = ('part', 'template', 'data')


admin.site.register(Part, PartAdmin)
admin.site.register(PartCategory, PartCategoryAdmin)
admin.site.register(PartAttachment, PartAttachmentAdmin)
admin.site.register(PartStar, PartStarAdmin)
admin.site.register(BomItem, BomItemAdmin)
admin.site.register(PartParameterTemplate, ParameterTemplateAdmin)
admin.site.register(PartParameter, ParameterAdmin)
admin.site.register(PartTestTemplate, PartTestTemplateAdmin)
