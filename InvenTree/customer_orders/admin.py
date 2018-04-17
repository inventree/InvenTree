from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import CustomerOrder, CustomerOrderLine


class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ('internal_ref',)

class CustomerOrderLineAdmin(admin.ModelAdmin):
    list_display = ('customer_order', 'line_number')


admin.site.register(CustomerOrder, CustomerOrderAdmin)
admin.site.register(CustomerOrderLine, CustomerOrderLineAdmin)