from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Customer, CustomerOrder, CustomerOrderLine


class CustomerAdmin(ImportExportModelAdmin):
    list_display = ('name', 'website', 'contact')


class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ('internal_ref',)


class CustomerOrderLineAdmin(admin.ModelAdmin):
    list_display = ('customer_order', 'line_number')


admin.site.register(Customer, CustomerAdmin)
admin.site.register(CustomerOrder, CustomerOrderAdmin)
admin.site.register(CustomerOrderLine, CustomerOrderLineAdmin)