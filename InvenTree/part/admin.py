"""Admin class definitions for the 'part' app"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from import_export import widgets
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field

from company.models import SupplierPart
from InvenTree.admin import InvenTreeResource
from part import models
from stock.models import StockLocation


class PartResource(InvenTreeResource):
    """Class for managing Part data import/export."""

    class Meta:
        """Metaclass definition"""

        model = models.Part
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True
        exclude = [
            'bom_checksum',
            'bom_checked_by',
            'bom_checked_date',
            'lft',
            'rght',
            'tree_id',
            'level',
            'metadata',
            'barcode_data',
            'barcode_hash',
        ]

    id = Field(attribute='pk', column_name=_('Part ID'), widget=widgets.IntegerWidget())
    name = Field(
        attribute='name', column_name=_('Part Name'), widget=widgets.CharWidget()
    )
    description = Field(
        attribute='description',
        column_name=_('Part Description'),
        widget=widgets.CharWidget(),
    )
    IPN = Field(attribute='IPN', column_name=_('IPN'), widget=widgets.CharWidget())
    revision = Field(
        attribute='revision', column_name=_('Revision'), widget=widgets.CharWidget()
    )
    keywords = Field(
        attribute='keywords', column_name=_('Keywords'), widget=widgets.CharWidget()
    )
    link = Field(attribute='link', column_name=_('Link'), widget=widgets.CharWidget())
    units = Field(
        attribute='units', column_name=_('Units'), widget=widgets.CharWidget()
    )
    notes = Field(attribute='notes', column_name=_('Notes'))
    image = Field(attribute='image', column_name=_('Part Image'), readonly=True)
    category = Field(
        attribute='category',
        column_name=_('Category ID'),
        widget=widgets.ForeignKeyWidget(models.PartCategory),
    )
    category_name = Field(
        attribute='category__name', column_name=_('Category Name'), readonly=True
    )
    default_location = Field(
        attribute='default_location',
        column_name=_('Default Location ID'),
        widget=widgets.ForeignKeyWidget(StockLocation),
    )
    default_supplier = Field(
        attribute='default_supplier',
        column_name=_('Default Supplier ID'),
        widget=widgets.ForeignKeyWidget(SupplierPart),
    )
    variant_of = Field(
        attribute='variant_of',
        column_name=_('Variant Of'),
        widget=widgets.ForeignKeyWidget(models.Part),
    )
    minimum_stock = Field(attribute='minimum_stock', column_name=_('Minimum Stock'))

    # Part Attributes
    active = Field(
        attribute='active', column_name=_('Active'), widget=widgets.BooleanWidget()
    )
    assembly = Field(
        attribute='assembly', column_name=_('Assembly'), widget=widgets.BooleanWidget()
    )
    component = Field(
        attribute='component',
        column_name=_('Component'),
        widget=widgets.BooleanWidget(),
    )
    purchaseable = Field(
        attribute='purchaseable',
        column_name=_('Purchaseable'),
        widget=widgets.BooleanWidget(),
    )
    salable = Field(
        attribute='salable', column_name=_('Salable'), widget=widgets.BooleanWidget()
    )
    is_template = Field(
        attribute='is_template',
        column_name=_('Template'),
        widget=widgets.BooleanWidget(),
    )
    trackable = Field(
        attribute='trackable',
        column_name=_('Trackable'),
        widget=widgets.BooleanWidget(),
    )
    virtual = Field(
        attribute='virtual', column_name=_('Virtual'), widget=widgets.BooleanWidget()
    )

    # Extra calculated meta-data (readonly)
    suppliers = Field(
        attribute='supplier_count', column_name=_('Suppliers'), readonly=True
    )
    in_stock = Field(
        attribute='total_stock',
        column_name=_('In Stock'),
        readonly=True,
        widget=widgets.IntegerWidget(),
    )
    on_order = Field(
        attribute='on_order',
        column_name=_('On Order'),
        readonly=True,
        widget=widgets.IntegerWidget(),
    )
    used_in = Field(
        attribute='used_in_count',
        column_name=_('Used In'),
        readonly=True,
        widget=widgets.IntegerWidget(),
    )
    allocated = Field(
        attribute='allocation_count',
        column_name=_('Allocated'),
        readonly=True,
        widget=widgets.IntegerWidget(),
    )
    building = Field(
        attribute='quantity_being_built',
        column_name=_('Building'),
        readonly=True,
        widget=widgets.IntegerWidget(),
    )
    min_cost = Field(
        attribute='pricing__overall_min', column_name=_('Minimum Cost'), readonly=True
    )
    max_cost = Field(
        attribute='pricing__overall_max', column_name=_('Maximum Cost'), readonly=True
    )

    def dehydrate_min_cost(self, part):
        """Render minimum cost value for this Part"""
        min_cost = part.pricing.overall_min if part.pricing else None

        if min_cost is not None:
            return float(min_cost.amount)

    def dehydrate_max_cost(self, part):
        """Render maximum cost value for this Part"""
        max_cost = part.pricing.overall_max if part.pricing else None

        if max_cost is not None:
            return float(max_cost.amount)

    def get_queryset(self):
        """Prefetch related data for quicker access."""
        query = super().get_queryset()
        query = query.prefetch_related(
            'category',
            'used_in',
            'builds',
            'supplier_parts__purchase_order_line_items',
            'stock_items__allocations',
        )

        return query

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        """Rebuild MPTT tree structure after importing Part data"""
        super().after_import(dataset, result, using_transactions, dry_run, **kwargs)

        # Rebuild the Part tree(s)
        models.Part.objects.rebuild()


class PartImportResource(InvenTreeResource):
    """Class for managing Part data import/export."""

    class Meta(PartResource.Meta):
        """Metaclass definition"""

        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True
        exclude = [
            'id',
            'category__name',
            'creation_date',
            'creation_user',
            'pricing__overall_min',
            'pricing__overall_max',
            'bom_checksum',
            'bom_checked_by',
            'bom_checked_date',
            'lft',
            'rght',
            'tree_id',
            'level',
            'metadata',
            'barcode_data',
            'barcode_hash',
        ]


class PartParameterInline(admin.TabularInline):
    """Inline for part parameter data"""

    model = models.PartParameter


class PartAdmin(ImportExportModelAdmin):
    """Admin class for the Part model"""

    resource_class = PartResource

    list_display = ('full_name', 'description', 'total_stock', 'category')

    list_filter = ('active', 'assembly', 'is_template', 'virtual')

    search_fields = (
        'name',
        'description',
        'category__name',
        'category__description',
        'IPN',
    )

    autocomplete_fields = [
        'variant_of',
        'category',
        'default_location',
        'default_supplier',
    ]

    inlines = [PartParameterInline]


class PartPricingAdmin(admin.ModelAdmin):
    """Admin class for PartPricing model"""

    list_display = ('part', 'overall_min', 'overall_max')

    autcomplete_fields = ['part']


class PartStocktakeAdmin(admin.ModelAdmin):
    """Admin class for PartStocktake model"""

    list_display = ['part', 'date', 'quantity', 'user']


class PartStocktakeReportAdmin(admin.ModelAdmin):
    """Admin class for PartStocktakeReport model"""

    list_display = ['date', 'user']


class PartCategoryResource(InvenTreeResource):
    """Class for managing PartCategory data import/export."""

    class Meta:
        """Metaclass definition"""

        model = models.PartCategory
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

        exclude = [
            # Exclude MPTT internal model fields
            'lft',
            'rght',
            'tree_id',
            'level',
            'metadata',
            'icon',
        ]

    id = Field(
        attribute='pk', column_name=_('Category ID'), widget=widgets.IntegerWidget()
    )
    name = Field(attribute='name', column_name=_('Category Name'))
    description = Field(attribute='description', column_name=_('Description'))
    parent = Field(
        attribute='parent',
        column_name=_('Parent ID'),
        widget=widgets.ForeignKeyWidget(models.PartCategory),
    )
    parent_name = Field(
        attribute='parent__name', column_name=_('Parent Name'), readonly=True
    )
    default_location = Field(
        attribute='default_location',
        column_name=_('Default Location ID'),
        widget=widgets.ForeignKeyWidget(StockLocation),
    )
    default_keywords = Field(attribute='default_keywords', column_name=_('Keywords'))
    pathstring = Field(attribute='pathstring', column_name=_('Category Path'))

    # Calculated fields
    parts = Field(
        attribute='item_count',
        column_name=_('Parts'),
        widget=widgets.IntegerWidget(),
        readonly=True,
    )

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        """Rebuild MPTT tree structure after importing PartCategory data"""
        super().after_import(dataset, result, using_transactions, dry_run, **kwargs)

        # Rebuild the PartCategory tree(s)
        models.PartCategory.objects.rebuild()


class PartCategoryAdmin(ImportExportModelAdmin):
    """Admin class for the PartCategory model"""

    resource_class = PartCategoryResource

    list_display = ('name', 'pathstring', 'description')

    search_fields = ('name', 'description')

    autocomplete_fields = ('parent', 'default_location')


class PartRelatedAdmin(admin.ModelAdmin):
    """Class to manage PartRelated objects."""

    autocomplete_fields = ('part_1', 'part_2')


class PartAttachmentAdmin(admin.ModelAdmin):
    """Admin class for the PartAttachment model"""

    list_display = ('part', 'attachment', 'comment')

    autocomplete_fields = ('part',)


class PartTestTemplateAdmin(admin.ModelAdmin):
    """Admin class for the PartTestTemplate model"""

    list_display = ('part', 'test_name', 'required')

    autocomplete_fields = ('part',)


class BomItemResource(InvenTreeResource):
    """Class for managing BomItem data import/export."""

    class Meta:
        """Metaclass definition"""

        model = models.BomItem
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

        exclude = ['checksum', 'id', 'part', 'sub_part', 'validated']

    level = Field(attribute='level', column_name=_('BOM Level'), readonly=True)

    bom_id = Field(
        attribute='pk', column_name=_('BOM Item ID'), widget=widgets.IntegerWidget()
    )

    # ID of the parent part
    parent_part_id = Field(
        attribute='part',
        column_name=_('Parent ID'),
        widget=widgets.ForeignKeyWidget(models.Part),
    )
    parent_part_ipn = Field(
        attribute='part__IPN', column_name=_('Parent IPN'), readonly=True
    )
    parent_part_name = Field(
        attribute='part__name', column_name=_('Parent Name'), readonly=True
    )
    part_id = Field(
        attribute='sub_part',
        column_name=_('Part ID'),
        widget=widgets.ForeignKeyWidget(models.Part),
    )
    part_ipn = Field(
        attribute='sub_part__IPN', column_name=_('Part IPN'), readonly=True
    )
    part_name = Field(
        attribute='sub_part__name', column_name=_('Part Name'), readonly=True
    )
    part_description = Field(
        attribute='sub_part__description', column_name=_('Description'), readonly=True
    )
    quantity = Field(attribute='quantity', column_name=_('Quantity'))
    reference = Field(attribute='reference', column_name=_('Reference'))
    note = Field(attribute='note', column_name=_('Note'))
    min_cost = Field(
        attribute='sub_part__pricing__overall_min',
        column_name=_('Minimum Price'),
        readonly=True,
    )
    max_cost = Field(
        attribute='sub_part__pricing__overall_max',
        column_name=_('Maximum Price'),
        readonly=True,
    )

    sub_assembly = Field(
        attribute='sub_part__assembly', column_name=_('Assembly'), readonly=True
    )

    def dehydrate_min_cost(self, item):
        """Render minimum cost value for the BOM line item"""
        min_price = item.sub_part.pricing.overall_min if item.sub_part.pricing else None

        if min_price is not None:
            return float(min_price.amount) * float(item.quantity)

    def dehydrate_max_cost(self, item):
        """Render maximum cost value for the BOM line item"""
        max_price = item.sub_part.pricing.overall_max if item.sub_part.pricing else None

        if max_price is not None:
            return float(max_price.amount) * float(item.quantity)

    def dehydrate_quantity(self, item):
        """Special consideration for the 'quantity' field on data export. We do not want a spreadsheet full of "1.0000" (we'd rather "1")

        Ref: https://django-import-export.readthedocs.io/en/latest/getting_started.html#advanced-data-manipulation-on-export
        """
        return float(item.quantity)

    def before_export(self, queryset, *args, **kwargs):
        """Perform before exporting data"""
        self.is_importing = kwargs.get('importing', False)
        self.include_pricing = kwargs.pop('include_pricing', False)

    def get_fields(self, **kwargs):
        """If we are exporting for the purposes of generating a 'bom-import' template, there are some fields which we are not interested in."""
        fields = super().get_fields(**kwargs)

        is_importing = getattr(self, 'is_importing', False)
        include_pricing = getattr(self, 'include_pricing', False)

        to_remove = ['metadata']

        if is_importing or not include_pricing:
            # Remove pricing fields in this instance
            to_remove += [
                'sub_part__pricing__overall_min',
                'sub_part__pricing__overall_max',
            ]

        if is_importing:
            to_remove += [
                'level',
                'pk',
                'part',
                'part__IPN',
                'part__name',
                'sub_part__name',
                'sub_part__description',
                'sub_part__assembly',
            ]

        idx = 0

        while idx < len(fields):
            if fields[idx].attribute in to_remove:
                del fields[idx]
            else:
                idx += 1

        return fields


class BomItemAdmin(ImportExportModelAdmin):
    """Admin class for the BomItem model"""

    resource_class = BomItemResource

    list_display = ('part', 'sub_part', 'quantity')

    search_fields = (
        'part__name',
        'part__description',
        'sub_part__name',
        'sub_part__description',
    )

    autocomplete_fields = ('part', 'sub_part')


class ParameterTemplateResource(InvenTreeResource):
    """Class for managing ParameterTemplate import/export"""

    # The following fields will be converted from None to ''
    CONVERT_NULL_FIELDS = ['choices', 'units']

    class Meta:
        """Metaclass definition"""

        model = models.PartParameterTemplate
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

        exclude = ['metadata']


class ParameterTemplateAdmin(ImportExportModelAdmin):
    """Admin class for the PartParameterTemplate model"""

    resource_class = ParameterTemplateResource

    list_display = ('name', 'units')

    search_fields = ('name', 'units')


class ParameterResource(InvenTreeResource):
    """Class for managing PartParameter data import/export."""

    class Meta:
        """Metaclass definition"""

        model = models.PartParameter
        skip_unchanged = True
        report_skipped = False
        clean_model_instance = True

    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(models.Part))

    part_name = Field(attribute='part__name', readonly=True)

    template = Field(
        attribute='template',
        widget=widgets.ForeignKeyWidget(models.PartParameterTemplate),
    )

    template_name = Field(attribute='template__name', readonly=True)


class ParameterAdmin(ImportExportModelAdmin):
    """Admin class for the PartParameter model"""

    resource_class = ParameterResource

    list_display = ('part', 'template', 'data')

    autocomplete_fields = ('part', 'template')


class PartCategoryParameterAdmin(admin.ModelAdmin):
    """Admin class for the PartCategoryParameterTemplate model"""

    autocomplete_fields = ('category', 'parameter_template')


class PartSellPriceBreakAdmin(admin.ModelAdmin):
    """Admin class for the PartSellPriceBreak model"""

    class Meta:
        """Metaclass definition"""

        model = models.PartSellPriceBreak

    list_display = ('part', 'quantity', 'price')


class PartInternalPriceBreakAdmin(admin.ModelAdmin):
    """Admin class for the PartInternalPriceBreak model"""

    class Meta:
        """Metaclass definition"""

        model = models.PartInternalPriceBreak

    list_display = ('part', 'quantity', 'price')

    autocomplete_fields = ('part',)


admin.site.register(models.Part, PartAdmin)
admin.site.register(models.PartCategory, PartCategoryAdmin)
admin.site.register(models.PartRelated, PartRelatedAdmin)
admin.site.register(models.PartAttachment, PartAttachmentAdmin)
admin.site.register(models.BomItem, BomItemAdmin)
admin.site.register(models.PartParameterTemplate, ParameterTemplateAdmin)
admin.site.register(models.PartParameter, ParameterAdmin)
admin.site.register(models.PartCategoryParameterTemplate, PartCategoryParameterAdmin)
admin.site.register(models.PartTestTemplate, PartTestTemplateAdmin)
admin.site.register(models.PartSellPriceBreak, PartSellPriceBreakAdmin)
admin.site.register(models.PartInternalPriceBreak, PartInternalPriceBreakAdmin)
admin.site.register(models.PartPricing, PartPricingAdmin)
admin.site.register(models.PartStocktake, PartStocktakeAdmin)
admin.site.register(models.PartStocktakeReport, PartStocktakeReportAdmin)
