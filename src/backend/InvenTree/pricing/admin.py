"""Admin class definitions for the pricing app."""

from django.contrib import admin

from .models import StockItemCost, StockItemCostEntry


@admin.register(StockItemCostEntry)
class StockItemCostEntryAdmin(admin.ModelAdmin):
    """Admin class for the StockItemCostEntry model."""

    list_display = ['stock_item', 'cost_type', 'min_cost', 'max_cost', 'date']

    list_filter = ['cost_type']

    autocomplete_fields = ['stock_item', 'user']


@admin.register(StockItemCost)
class StockItemCostAdmin(admin.ModelAdmin):
    """Admin class for the (read-only, calculated) StockItemCost summary model."""

    list_display = ['stock_item', 'min_cost', 'max_cost', 'date']

    autocomplete_fields = ['stock_item']

    def has_add_permission(self, request):
        """This model is calculated automatically - do not allow manual creation."""
        return False

    def has_change_permission(self, request, obj=None):
        """This model is calculated automatically - do not allow manual editing."""
        return False
