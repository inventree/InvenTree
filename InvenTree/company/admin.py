from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Company
#from .models import SupplierOrder

class CompanyAdmin(ImportExportModelAdmin):
    list_display = ('name', 'website', 'contact')


#class SupplierOrderAdmin(admin.ModelAdmin):
#    list_display = ('internal_ref', 'supplier', 'issued_date', 'delivery_date', 'status')


admin.site.register(Company, CompanyAdmin)
#admin.site.register(SupplierOrder, SupplierOrderAdmin)
