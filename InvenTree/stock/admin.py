from django.contrib import admin

from .models import StockLocation, StockItem


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'description')


class StockItemAdmin(admin.ModelAdmin):
    list_display = ('part', 'quantity', 'location', 'status', 'updated')


admin.site.register(StockLocation, LocationAdmin)
admin.site.register(StockItem, StockItemAdmin)
