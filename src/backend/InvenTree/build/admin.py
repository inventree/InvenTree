"""Admin functionality for the BuildOrder app."""

from django.contrib import admin

from build.models import Build, BuildItem, BuildLine


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

    autocomplete_fields = ['build_line', 'stock_item', 'install_into']


@admin.register(BuildLine)
class BuildLineAdmin(admin.ModelAdmin):
    """Class for managing the BuildLine model via the admin interface."""

    list_display = ('build', 'bom_item', 'quantity')

    search_fields = ['build__title', 'build__reference', 'bom_item__sub_part__name']

    autocomplete_fields = ['bom_item', 'build']
