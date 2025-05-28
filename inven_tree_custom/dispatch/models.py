# inven_tree_custom/dispatch/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# We need to reference StockItem.
# Assuming 'stock.StockItem' is the correct way to reference InvenTree's StockItem model.
# If the plugin is loaded after the 'stock' app, this string reference should work.
STOCK_ITEM_MODEL_PATH = 'stock.StockItem'

class Dispatch(models.Model):
    """
    Represents a dispatch event, grouping several stock items for a client.
    """
    client = models.CharField(
        max_length=200,
        blank=False,
        null=False,
        verbose_name=_("Client Name"),
        help_text=_("Name of the client receiving the dispatch")
    )
    date = models.DateField(
        default=timezone.now, # Default to current date
        verbose_name=_("Dispatch Date"),
        help_text=_("Date of the dispatch")
    )
    # Add any other fields relevant to a dispatch header
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dispatch to {self.client} on {self.date.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = _("Dispatch")
        verbose_name_plural = _("Dispatches")
        # Example: ordering by date descending
        ordering = ['-date', '-created_at']


class DispatchItem(models.Model):
    """
    Represents an individual stock item included in a dispatch.
    Ensures that a StockItem is unique per Dispatch.
    """
    dispatch = models.ForeignKey(
        Dispatch,
        related_name='items', # Allows accessing items from a Dispatch instance via dispatch.items
        on_delete=models.CASCADE, # If a dispatch is deleted, its items are also deleted
        verbose_name=_("Dispatch")
    )
    stock_item = models.ForeignKey(
        STOCK_ITEM_MODEL_PATH,
        on_delete=models.PROTECT, # Prevent deletion of StockItem if it's part of a dispatch
                                  # Or models.SET_NULL if appropriate, but PROTECT is safer.
        verbose_name=_("Stock Item"),
        help_text=_("The specific stock item being dispatched")
    )
    quantity = models.DecimalField( # Assuming quantity might not always be 1, or could be fractional
        max_digits=10,
        decimal_places=2, # Adjust as per typical quantities
        default=1.0,
        verbose_name=_("Quantity Dispatched"),
        help_text=_("Quantity of this stock item dispatched")
    )
    # Add any other fields relevant to a dispatch line item, e.g., notes per item
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Attempt to get a meaningful representation of the stock_item
        # This might require stock_item to be loaded if it's a string reference
        stock_item_repr = str(self.stock_item_id) # Default to ID
        if hasattr(self.stock_item, '__str__'):
             stock_item_repr = str(self.stock_item)

        return f"Item {stock_item_repr} for {self.dispatch}"

    class Meta:
        verbose_name = _("Dispatch Item")
        verbose_name_plural = _("Dispatch Items")
        # Unique constraint: A specific StockItem can only appear once per Dispatch.
        unique_together = [['dispatch', 'stock_item']]
        ordering = ['added_at']
