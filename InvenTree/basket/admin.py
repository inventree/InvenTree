from django.contrib import admin
from .models import SalesOrderBasket
from import_export.admin import ImportExportModelAdmin
# Register your models here.

class SalesOrderBsketAdmin(ImportExportModelAdmin):

    resource_class = SalesOrderBasket

    list_display = (
        'name',
        'status',
        'creation_date',
    )
admin.site.register(SalesOrderBasket, SalesOrderBsketAdmin)