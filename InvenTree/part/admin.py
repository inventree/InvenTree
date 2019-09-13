from django.contrib import admin
from import_export.admin import ImportExportModelAdmin, ImportExportActionModelAdmin
from import_export.resources import ModelResource
from import_export.fields import Field
import import_export.widgets as widgets

from .models import PartCategory, Part
from .models import PartAttachment, PartStar
from .models import BomItem
from .models import PartParameterTemplate, PartParameter

from stock.models import StockLocation
from company.models import SupplierPart


class PartResource(ModelResource):
    """ Class for managing Part data import/export """

    # Constuct some extra fields for export
    category = Field(attribute='category', widget=widgets.ForeignKeyWidget(PartCategory))
    
    default_location = Field(attribute='default_location', widget=widgets.ForeignKeyWidget(StockLocation))

    category_name = Field(attribute='category__name', readonly=True)
    
    variant_of = Field(attribute='variant_of', widget=widgets.ForeignKeyWidget(Part))

    class Meta:
        model = Part
        skip_unchanged = True
        report_skipped = False
        exclude = [
            'bom_checksum', 'bom_checked_by', 'bom_checked_date'
        ]


class PartAdmin(ImportExportModelAdmin):

    resource_class = PartResource

    list_display = ('full_name', 'description', 'total_stock', 'category')


class PartCategoryResource(ModelResource):
    """ Class for managing PartCategory data import/export """

    parent = Field(attribute='parent', widget=widgets.ForeignKeyWidget(PartCategory))

    default_location = Field(attribute='default_location', widget=widgets.ForeignKeyWidget(StockLocation))

    parent_name = Field(attribute='parent__name', readonly=True)

    class Meta:
        model = PartCategory
        skip_unchanged = True
        report_skipped = False

        exclude = [
            # Exclude MPTT internal model fields
            'lft', 'rght', 'tree_id', 'level',
        ]

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):

        super().after_import(dataset, result, using_transactions, dry_run, **kwargs)

        print("Rebuilding PartCategory tree")
        # Rebuild teh PartCategory tree
        PartCategory.objects.rebuild()
        print("Done!")

class PartCategoryAdmin(ImportExportModelAdmin):

    resource_class = PartCategoryResource

    list_display = ('name', 'pathstring', 'description')


class PartAttachmentAdmin(admin.ModelAdmin):

    list_display = ('part', 'attachment', 'comment')


class PartStarAdmin(admin.ModelAdmin):

    list_display = ('part', 'user')


class BomItemAdmin(ImportExportModelAdmin):
    list_display = ('part', 'sub_part', 'quantity')


class ParameterTemplateAdmin(ImportExportModelAdmin):
    list_display = ('name', 'units')


class ParameterAdmin(ImportExportModelAdmin):
    list_display = ('part', 'template', 'data')


admin.site.register(Part, PartAdmin)
admin.site.register(PartCategory, PartCategoryAdmin)
admin.site.register(PartAttachment, PartAttachmentAdmin)
admin.site.register(PartStar, PartStarAdmin)
admin.site.register(BomItem, BomItemAdmin)
admin.site.register(PartParameterTemplate, ParameterTemplateAdmin)
admin.site.register(PartParameter, ParameterAdmin)
