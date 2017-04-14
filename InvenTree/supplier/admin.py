from django.contrib import admin

from .models import Supplier, SupplierPart, Customer, Manufacturer


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'contact')


admin.site.register(Customer, CompanyAdmin)
admin.site.register(Supplier, CompanyAdmin)
admin.site.register(Manufacturer, CompanyAdmin)
admin.site.register(SupplierPart)
