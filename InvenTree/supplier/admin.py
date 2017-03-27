from django.contrib import admin

from .models import Supplier, SupplierPart

admin.site.register(Supplier)
admin.site.register(SupplierPart)