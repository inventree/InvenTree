from django.contrib import admin

from .models import Warehouse, StockItem

admin.site.register(Warehouse)
admin.site.register(StockItem)