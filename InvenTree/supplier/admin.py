from django.contrib import admin

from .models import Supplier, SupplierPart

class SupplierAdmin(admin.ModelAdmin):
    list_display=('name','URL','contact')

admin.site.register(Supplier, SupplierAdmin)
admin.site.register(SupplierPart)