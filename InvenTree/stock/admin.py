from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import StockLocation, StockItem
from .models import StockItemTracking


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'pathstring', 'description')


class StockItemAdmin(SimpleHistoryAdmin):
    list_display = ('part', 'quantity', 'location', 'status', 'updated')


class StockTrackingAdmin(admin.ModelAdmin):
    list_display = ('item', 'date', 'title')


admin.site.register(StockLocation, LocationAdmin)
admin.site.register(StockItem, StockItemAdmin)
admin.site.register(StockItemTracking, StockTrackingAdmin)
