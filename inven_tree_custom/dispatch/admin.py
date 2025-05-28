# inven_tree_custom/dispatch/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _ # For custom field descriptions
from .models import Dispatch, DispatchItem

class DispatchItemInline(admin.TabularInline):
    """
    Allows editing DispatchItems directly within the Dispatch admin page.
    """
    model = DispatchItem
    extra = 1  # Number of empty forms to display for adding new items
    # autocomplete_fields = ['stock_item'] # If StockItem has a search_fields defined in its admin
    raw_id_fields = ['stock_item'] # More robust for selecting StockItems
    readonly_fields = ['added_at']
    # Define which fields to show in the inline form, if needed
    # fields = ('stock_item', 'quantity') 

@admin.register(Dispatch)
class DispatchAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for the Dispatch model.
    """
    list_display = ('client', 'date', 'get_item_count', 'created_at')
    list_filter = ('date', 'client')
    search_fields = ('client',)
    date_hierarchy = 'date'
    inlines = [DispatchItemInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('client', 'date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',) # Collapsible section
        }),
    )

    def get_item_count(self, obj):
        return obj.items.count()
    get_item_count.short_description = _('Number of Items')

@admin.register(DispatchItem)
class DispatchItemAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for the DispatchItem model.
    Typically, items are managed via the DispatchAdmin inline,
    but a separate admin can be useful for direct inspection or management.
    """
    list_display = ('dispatch', 'get_stock_item_display', 'quantity', 'added_at')
    list_filter = ('dispatch__date', 'dispatch__client') # Filter by properties of the related Dispatch
    search_fields = ('stock_item__serial', 'stock_item__part__name') # Example: search by StockItem serial or Part name
                                                                # This assumes StockItem has 'serial' and 'part' FK with 'name'
    raw_id_fields = ['stock_item', 'dispatch'] # Useful for selecting foreign keys
    readonly_fields = ['added_at']
    # list_select_related = ('dispatch', 'stock_item', 'stock_item__part') # For performance if displaying related fields

    def get_stock_item_display(self, obj):
        # Return a user-friendly representation of the stock_item
        # This depends on how StockItem is stringified or what fields it has
        if obj.stock_item:
            # Assuming stock_item might have a 'part' attribute and 'serial' or 'name'
            # This needs to be adjusted to how InvenTree's StockItem can be best represented.
            # For instance, if StockItem has a __str__ method that's good, use that.
            # Or access specific fields like part name and serial number.
            return f"{obj.stock_item}" # Default to its __str__
        return "-"
    get_stock_item_display.short_description = _('Stock Item')
    # If you want to allow ordering by this custom field, you'd need to set admin_order_field
    # get_stock_item_display.admin_order_field = 'stock_item' # or specific field on stock_item
