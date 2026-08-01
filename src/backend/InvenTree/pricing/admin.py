"""Admin class definitions for the pricing app."""

from django.contrib import admin

from .models import StockItemCost


@admin.register(StockItemCost)
class StockItemCostAdmin(admin.ModelAdmin):
    """Admin class for the StockItemCost model."""

    list_display = ['stock_item', 'part', 'cost_type', 'min_cost', 'max_cost', 'date']

    list_filter = ['cost_type']

    autocomplete_fields = ['stock_item', 'part', 'user']
