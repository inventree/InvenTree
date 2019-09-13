from django.contrib import admin
from import_export.admin import ImportExportModelAdmin, ImportExportActionModelAdmin
from import_export.resources import ModelResource
from import_export.fields import Field

from .models import PartCategory, Part
from .models import PartAttachment, PartStar
from .models import BomItem
from .models import PartParameterTemplate, PartParameter


class PartResource(ModelResource):
    """ Class for managing Part model export """

    # Constuct some extra fields for export
    category = Field(attribute='category__pk', column_name='Category')
    
    category_name = Field(attribute='category__name', column_name='Category Name')
    
    default_location = Field(attribute='default_location__pk', column_name='Default Location')
    
    default_supplier = Field(attribute='default_supplier__pk', column_name='Default Supplier')

    in_stock = Field(attribute='total_stock')

    on_order = Field(attribute='on_order')

    variant_of = Field(attribute='variant_of__pk')

    class Meta:
        model = Part
        exclude = [
            'bom_checksum', 'bom_checked_by', 'bom_checked_date'
        ]


class PartAdmin(ImportExportModelAdmin):

    resource_class = PartResource

    list_display = ('full_name', 'description', 'total_stock', 'category')


class PartCategoryAdmin(ImportExportModelAdmin):

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
