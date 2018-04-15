from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import PartCategory, Part
from .models import BomItem
from .models import PartAttachment


class PartAdmin(ImportExportModelAdmin):

    list_display = ('name', 'IPN', 'description', 'stock', 'category')


class PartCategoryAdmin(admin.ModelAdmin):

    list_display = ('name', 'pathstring', 'description')


class BomItemAdmin(ImportExportModelAdmin):
    list_display = ('part', 'sub_part', 'quantity')


class PartAttachmentAdmin(admin.ModelAdmin):
    list_display = ('part', 'attachment')


"""
class ParameterTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'units', 'format')


class ParameterAdmin(admin.ModelAdmin):
    list_display = ('part', 'template', 'value')
"""

admin.site.register(Part, PartAdmin)
admin.site.register(PartCategory, PartCategoryAdmin)
admin.site.register(BomItem, BomItemAdmin)
admin.site.register(PartAttachment, PartAttachmentAdmin)

# admin.site.register(PartParameter, ParameterAdmin)
# admin.site.register(PartParameterTemplate, ParameterTemplateAdmin)
# admin.site.register(CategoryParameterLink)
