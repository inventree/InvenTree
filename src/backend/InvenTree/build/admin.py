"""Admin functionality for the BuildOrder app."""

from django.contrib import admin

from build.models import (
    Build,
    BuildItem,
    BuildLine,
    NonConformance,
    NonConformanceStockItem,
)


@admin.register(Build)
class BuildAdmin(admin.ModelAdmin):
    """Class for managing the Build model via the admin interface."""

    exclude = ['reference_int']

    list_display = ('reference', 'title', 'part', 'status', 'batch', 'quantity')

    search_fields = ['reference', 'title', 'part__name', 'part__description']

    autocomplete_fields = [
        'completed_by',
        'destination',
        'parent',
        'part',
        'project_code',
        'responsible',
        'sales_order',
        'take_from',
    ]


@admin.register(BuildItem)
class BuildItemAdmin(admin.ModelAdmin):
    """Class for managing the BuildItem model via the admin interface."""

    list_display = ('stock_item', 'quantity')

    search_fields = [
        'build_line__build__reference',
        'build_line__build__title',
        'stock_item__part__name',
        'stock_item__serial',
    ]

    autocomplete_fields = ['build_line', 'stock_item', 'install_into']


@admin.register(BuildLine)
class BuildLineAdmin(admin.ModelAdmin):
    """Class for managing the BuildLine model via the admin interface."""

    list_display = ('build', 'bom_item', 'quantity')

    search_fields = ['build__title', 'build__reference', 'bom_item__sub_part__name']

    autocomplete_fields = ['bom_item', 'build']


@admin.register(NonConformance)
class NonConformanceAdmin(admin.ModelAdmin):
    """Class for managing the NonConformance model via the admin interface."""

    exclude = ['reference_int']

    list_display = ('reference', 'description', 'part', 'status', 'disposition')

    search_fields = ['reference', 'description', 'part__name', 'part__description']

    autocomplete_fields = [
        'part',
        'build_order',
        'sales_order',
        'purchase_order',
        'return_order',
        'responsible',
        'raised_by',
    ]


@admin.register(NonConformanceStockItem)
class NonConformanceStockItemAdmin(admin.ModelAdmin):
    """Class for managing the NonConformanceStockItem model via the admin interface."""

    list_display = ('ncr', 'stock_item', 'quantity')

    autocomplete_fields = ['ncr', 'stock_item']
