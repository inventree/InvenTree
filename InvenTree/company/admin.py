from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Company
from .models import SupplierPart
from .models import SupplierPriceBreak


class CompanyAdmin(ImportExportModelAdmin):
    list_display = ('name', 'website', 'contact')


class SupplierPartAdmin(ImportExportModelAdmin):
    list_display = ('part', 'supplier', 'SKU')


class SupplierPriceBreakAdmin(ImportExportModelAdmin):
    list_display = ('part', 'quantity', 'cost')


admin.site.register(Company, CompanyAdmin)
admin.site.register(SupplierPart, SupplierPartAdmin)
admin.site.register(SupplierPriceBreak, SupplierPriceBreakAdmin)
