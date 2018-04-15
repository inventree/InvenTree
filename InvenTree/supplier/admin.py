from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Supplier, SupplierPart, Customer, Manufacturer


class CompanyAdmin(ImportExportModelAdmin):
    list_display = ('name', 'website', 'contact')


class SupplierPartAdmin(ImportExportModelAdmin):
    list_display = ('part', 'supplier', 'SKU')


admin.site.register(Customer, CompanyAdmin)
admin.site.register(Supplier, CompanyAdmin)
admin.site.register(Manufacturer, CompanyAdmin)
admin.site.register(SupplierPart, SupplierPartAdmin)
