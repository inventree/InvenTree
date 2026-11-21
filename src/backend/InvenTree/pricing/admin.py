"""Admin class definitions for the 'pricing' app."""

from django.contrib import admin

from pricing import models


@admin.register(models.PartPricing)
class PartPricingAdmin(admin.ModelAdmin):
    """Admin class for PartPricing model."""

    list_display = ('part', 'overall_min', 'overall_max')

    search_fields = ['part__name', 'part__IPN', 'part__description']

    autocomplete_fields = ['part']


@admin.register(models.PartSellPriceBreak)
class PartSellPriceBreakAdmin(admin.ModelAdmin):
    """Admin class for the PartSellPriceBreak model."""

    class Meta:
        """Metaclass options."""

        model = models.PartSellPriceBreak

    list_display = ('part', 'quantity', 'price')

    search_fields = ['part__name', 'part__IPN']

    autocomplete_fields = ('part',)


@admin.register(models.PartInternalPriceBreak)
class PartInternalPriceBreakAdmin(admin.ModelAdmin):
    """Admin class for the PartInternalPriceBreak model."""

    class Meta:
        """Metaclass options."""

        model = models.PartInternalPriceBreak

    list_display = ('part', 'quantity', 'price')

    search_fields = ['part__name', 'part__IPN']

    autocomplete_fields = ('part',)


@admin.register(models.StockItemCostEntry)
class StockItemCostEntryAdmin(admin.ModelAdmin):
    """Admin class for the StockItemCostEntry model."""

    list_display = (
        'stock_item',
        'cost_type',
        'source',
        'min_cost',
        'max_cost',
        'currency',
        'date',
    )

    list_filter = ('cost_type',)

    search_fields = ('source', 'notes')

    readonly_fields = ('converted_currency', 'converted_min_cost', 'converted_max_cost')

    autocomplete_fields = ('stock_item', 'user')

    def delete_queryset(self, request, queryset):
        """Delete the selected entries (bulk 'delete' action), and update the cost summaries.

        The default implementation calls queryset.delete(), which bypasses
        StockItemCostEntry.delete() - and would leave a stale StockItemCost summary.
        """
        models.StockItemCostEntry.objects.delete_costs(queryset)


@admin.register(models.StockItemCost)
class StockItemCostAdmin(admin.ModelAdmin):
    """Admin class for the StockItemCost summary model.

    This model is calculated automatically, and cannot be created or edited manually.
    """

    list_display = (
        'stock_item',
        'min_cost',
        'max_cost',
        'currency',
        'incomplete',
        'date',
    )

    list_filter = ('incomplete',)

    autocomplete_fields = ('stock_item',)

    def has_add_permission(self, request):
        """This model is calculated automatically - do not allow manual creation."""
        return False

    def has_change_permission(self, request, obj=None):
        """This model is calculated automatically - do not allow manual editing."""
        return False
