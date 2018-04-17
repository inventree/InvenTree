from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import CustomerOrder, CustomerOrderLine


class CustomerOrderAdmin(admin.ModelAdmin):
    pass

class CustomerOrderLineAdmin(admin.ModelAdmin):
    pass


admin.site.register(CustomerOrder, CustomerOrderAdmin)
admin.site.register(CustomerOrderLine, CustomerOrderLineAdmin)