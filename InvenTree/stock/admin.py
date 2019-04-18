from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import StockLocation, StockItem
from .models import StockItemTracking


class LocationAdmin(ImportExportModelAdmin):
    list_display = ('name', 'pathstring', 'description')


class StockItemAdmin(ImportExportModelAdmin):
    list_display = ('part', 'quantity', 'location', 'status', 'updated')


class StockTrackingAdmin(ImportExportModelAdmin):
    list_display = ('item', 'date', 'title')


admin.site.register(StockLocation, LocationAdmin)
admin.site.register(StockItem, StockItemAdmin)
admin.site.register(StockItemTracking, StockTrackingAdmin)
