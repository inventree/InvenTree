from django.contrib import admin

import import_export.widgets as widgets
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from import_export.resources import ModelResource

import part.models as models
from company.models import SupplierPart
from stock.models import StockLocation


class PartResource(ModelResource):
    """ Class for managing Part data import/export """

    # ForeignKey fields
    category = Field(attribute='category', widget=widgets.ForeignKeyWidget(models.PartCategory))

    default_location = Field(attribute='default_location', widget=widgets.ForeignKeyWidget(StockLocation))

    default_supplier = Field(attribute='default_supplier', widget=widgets.ForeignKeyWidget(SupplierPart))

    category_name = Field(attribute='category__name', readonly=True)

    variant_of = Field(attribute='variant_of', widget=widgets.ForeignKeyWidget(models.Part))

    suppliers = Field(attribute='supplier_count', readonly=True)

    # Extra calculated meta-data (readonly)
    in_stock = Field(attribute='total_stock', readonly=True, widget=widgets.IntegerWidget())

    on_order = Field(attribute='on_order', readonly=True, widget=widgets.IntegerWidget())

    used_in = Field(attribute='used_in_count', readonly=True, widget=widgets.IntegerWidget())

    allocated = Field(attribute='allocation_count', readonly=True, widget=widgets.IntegerWidget())

    building = Field(attribute='quantity_being_built', readonly=True, widget=widgets.IntegerWidget())

    class Meta:
        model = models.Part
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True
        exclude = [
            'bom_checksum', 'bom_checked_by', 'bom_checked_date',
            'lft', 'rght', 'tree_id', 'level',
            'metadata',
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

    autocomplete_fields = [
        'variant_of',
        'category',
        'default_location',
        'default_supplier',
    ]


class PartCategoryResource(ModelResource):
    """ Class for managing PartCategory data import/export """

    parent = Field(attribute='parent', widget=widgets.ForeignKeyWidget(models.PartCategory))

    parent_name = Field(attribute='parent__name', readonly=True)

    default_location = Field(attribute='default_location', widget=widgets.ForeignKeyWidget(StockLocation))

    class Meta:
        model = models.PartCategory
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

        exclude = [
            # Exclude MPTT internal model fields
            'lft', 'rght', 'tree_id', 'level',
            'metadata',
        ]

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):

        super().after_import(dataset, result, using_transactions, dry_run, **kwargs)

        # Rebuild the PartCategory tree(s)
        models.PartCategory.objects.rebuild()


class PartCategoryAdmin(ImportExportModelAdmin):

    resource_class = PartCategoryResource

    list_display = ('name', 'pathstring', 'description')

    search_fields = ('name', 'description')

    autocomplete_fields = ('parent', 'default_location',)


class PartRelatedAdmin(admin.ModelAdmin):
    """
    Class to manage PartRelated objects
    """

    autocomplete_fields = ('part_1', 'part_2')


class PartAttachmentAdmin(admin.ModelAdmin):

    list_display = ('part', 'attachment', 'comment')

    autocomplete_fields = ('part',)


class PartStarAdmin(admin.ModelAdmin):

    list_display = ('part', 'user')

    autocomplete_fields = ('part',)


class PartCategoryStarAdmin(admin.ModelAdmin):

    list_display = ('category', 'user')

    autocomplete_fields = ('category',)


class PartTestTemplateAdmin(admin.ModelAdmin):

    list_display = ('part', 'test_name', 'required')

    autocomplete_fields = ('part',)


class BomItemResource(ModelResource):
    """ Class for managing BomItem data import/export """

    level = Field(attribute='level', readonly=True)

    bom_id = Field(attribute='pk')

    # ID of the parent part
    parent_part_id = Field(attribute='part', widget=widgets.ForeignKeyWidget(models.Part))

    # IPN of the parent part
    parent_part_ipn = Field(attribute='part__IPN', readonly=True)

    # Name of the parent part
    parent_part_name = Field(attribute='part__name', readonly=True)

    # ID of the sub-part
    part_id = Field(attribute='sub_part', widget=widgets.ForeignKeyWidget(models.Part))

    # IPN of the sub-part
    part_ipn = Field(attribute='sub_part__IPN', readonly=True)

    # Name of the sub-part
    part_name = Field(attribute='sub_part__name', readonly=True)

    # Description of the sub-part
    part_description = Field(attribute='sub_part__description', readonly=True)

    # Is the sub-part itself an assembly?
    sub_assembly = Field(attribute='sub_part__assembly', readonly=True)

    def dehydrate_quantity(self, item):
        """
        Special consideration for the 'quantity' field on data export.
        We do not want a spreadsheet full of "1.0000" (we'd rather "1")

        Ref: https://django-import-export.readthedocs.io/en/latest/getting_started.html#advanced-data-manipulation-on-export
        """
        return float(item.quantity)

    def before_export(self, queryset, *args, **kwargs):

        self.is_importing = kwargs.get('importing', False)

    def get_fields(self, **kwargs):
        """
        If we are exporting for the purposes of generating
        a 'bom-import' template, there are some fields which
        we are not interested in.
        """

        fields = super().get_fields(**kwargs)

        # If we are not generating an "import" template,
        # just return the complete list of fields
        if not getattr(self, 'is_importing', False):
            return fields

        # Otherwise, remove some fields we are not interested in

        idx = 0

        to_remove = [
            'level',
            'bom_id',
            'parent_part_id',
            'parent_part_ipn',
            'parent_part_name',
            'part_description',
            'sub_assembly'
        ]

        while idx < len(fields):

            if fields[idx].column_name.lower() in to_remove:
                del fields[idx]
            else:
                idx += 1

        return fields

    class Meta:
        model = models.BomItem
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

    autocomplete_fields = ('part', 'sub_part',)


class ParameterTemplateAdmin(ImportExportModelAdmin):
    list_display = ('name', 'units')

    search_fields = ('name', 'units')


class ParameterResource(ModelResource):
    """ Class for managing PartParameter data import/export """

    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(models.Part))

    part_name = Field(attribute='part__name', readonly=True)

    template = Field(attribute='template', widget=widgets.ForeignKeyWidget(models.PartParameterTemplate))

    template_name = Field(attribute='template__name', readonly=True)

    class Meta:
        model = models.PartParameter
        skip_unchanged = True
        report_skipped = False
        clean_model_instance = True


class ParameterAdmin(ImportExportModelAdmin):

    resource_class = ParameterResource

    list_display = ('part', 'template', 'data')

    autocomplete_fields = ('part', 'template')


class PartCategoryParameterAdmin(admin.ModelAdmin):

    autocomplete_fields = ('category', 'parameter_template',)


class PartSellPriceBreakAdmin(admin.ModelAdmin):

    class Meta:
        model = models.PartSellPriceBreak

    list_display = ('part', 'quantity', 'price',)


class PartInternalPriceBreakAdmin(admin.ModelAdmin):

    class Meta:
        model = models.PartInternalPriceBreak

    list_display = ('part', 'quantity', 'price',)

    autocomplete_fields = ('part',)


admin.site.register(models.Part, PartAdmin)
admin.site.register(models.PartCategory, PartCategoryAdmin)
admin.site.register(models.PartRelated, PartRelatedAdmin)
admin.site.register(models.PartAttachment, PartAttachmentAdmin)
admin.site.register(models.PartStar, PartStarAdmin)
admin.site.register(models.PartCategoryStar, PartCategoryStarAdmin)
admin.site.register(models.BomItem, BomItemAdmin)
admin.site.register(models.PartParameterTemplate, ParameterTemplateAdmin)
admin.site.register(models.PartParameter, ParameterAdmin)
admin.site.register(models.PartCategoryParameterTemplate, PartCategoryParameterAdmin)
admin.site.register(models.PartTestTemplate, PartTestTemplateAdmin)
admin.site.register(models.PartSellPriceBreak, PartSellPriceBreakAdmin)
admin.site.register(models.PartInternalPriceBreak, PartInternalPriceBreakAdmin)
