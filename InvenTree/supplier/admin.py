from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Supplier, SupplierPart, Manufacturer


class SupplierAdmin(ImportExportModelAdmin):
    list_display = ('name', 'website', 'contact')


class ManufacturerAdmin(ImportExportModelAdmin):
    list_display = ('name', 'website', 'contact')


class SupplierPartAdmin(ImportExportModelAdmin):
    list_display = ('part', 'supplier', 'SKU')


admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(SupplierPart, SupplierPartAdmin)
