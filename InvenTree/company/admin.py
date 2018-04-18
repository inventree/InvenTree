from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Company, SupplierPart
from .models import SupplierOrder

class CompanyAdmin(ImportExportModelAdmin):
    list_display = ('name', 'website', 'contact')


class SupplierPartAdmin(ImportExportModelAdmin):
    list_display = ('part', 'supplier', 'SKU')


class SupplierOrderAdmin(admin.ModelAdmin):
    list_display = ('internal_ref', 'supplier', 'issued_date', 'delivery_date', 'status')


admin.site.register(Company, CompanyAdmin)
admin.site.register(SupplierPart, SupplierPartAdmin)
admin.site.register(SupplierOrder, SupplierOrderAdmin)
