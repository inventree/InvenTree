"""Admin for stock app."""

from django.contrib import admin
from django.db.models import Count

from .models import (
    StockItem,
    StockItemTestResult,
    StockItemTracking,
    StockLocation,
    StockLocationType,
)


class LocationInline(admin.TabularInline):
    """Inline for sub-locations."""

    model = StockLocation


@admin.register(StockLocation)
class LocationAdmin(admin.ModelAdmin):
    """Admin class for Location."""

    list_display = ('name', 'pathstring', 'description')

    search_fields = ('name', 'description')

    inlines = [LocationInline]

    autocomplete_fields = ['parent']


@admin.register(StockLocationType)
class LocationTypeAdmin(admin.ModelAdmin):
    """Admin class for StockLocationType."""

    list_display = ('name', 'description', 'icon', 'location_count')
    readonly_fields = ('location_count',)

    def get_queryset(self, request):
        """Annotate queryset to fetch location count."""
        return (
            super()
            .get_queryset(request)
            .annotate(location_count=Count('stock_locations'))
        )

    def location_count(self, obj):
        """Returns the number of locations this location type is assigned to."""
        return obj.location_count


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    """Admin class for StockItem."""

    list_display = ('part', 'quantity', 'location', 'status', 'updated')

    # A list of search fields which can be used for lookup on matching 'autocomplete' fields
    search_fields = ['part__name', 'part__description', 'serial', 'batch']

    autocomplete_fields = [
        'belongs_to',
        'build',
        'customer',
        'location',
        'parent',
        'part',
        'purchase_order',
        'sales_order',
        'stocktake_user',
        'supplier_part',
        'consumed_by',
    ]


@admin.register(StockItemTracking)
class StockTrackingAdmin(admin.ModelAdmin):
    """Admin class for StockTracking."""

    list_display = ('item', 'date', 'label')

    autocomplete_fields = ['item']


@admin.register(StockItemTestResult)
class StockItemTestResultAdmin(admin.ModelAdmin):
    """Admin class for StockItemTestResult."""

    list_display = ('stock_item', 'test_name', 'result', 'value')

    autocomplete_fields = ['stock_item']
