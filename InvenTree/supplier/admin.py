from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Supplier, SupplierPart, Manufacturer
from .models import SupplierOrder

class SupplierAdmin(ImportExportModelAdmin):
    list_display = ('name', 'website', 'contact')


class ManufacturerAdmin(ImportExportModelAdmin):
    list_display = ('name', 'website', 'contact')


class SupplierPartAdmin(ImportExportModelAdmin):
    list_display = ('part', 'supplier', 'SKU')


class SupplierOrderAdmin(admin.ModelAdmin):
    list_display = ('internal_ref', 'supplier', 'issued_date', 'delivery_date', 'status')


admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(SupplierPart, SupplierPartAdmin)
admin.site.register(SupplierOrder, SupplierOrderAdmin)
