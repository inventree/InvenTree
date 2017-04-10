from django.contrib import admin

from .models import Warehouse, StockItem


class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'description')


class StockItemAdmin(admin.ModelAdmin):
    list_display = ('part', 'quantity', 'location', 'status', 'updated')


admin.site.register(Warehouse, WarehouseAdmin)
admin.site.register(StockItem, StockItemAdmin)
