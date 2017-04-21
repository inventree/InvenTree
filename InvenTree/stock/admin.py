from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import StockLocation, StockItem


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'description')


class StockItemAdmin(SimpleHistoryAdmin):
    list_display = ('part', 'quantity', 'location', 'status', 'updated')


admin.site.register(StockLocation, LocationAdmin)
admin.site.register(StockItem, StockItemAdmin)
