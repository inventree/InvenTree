"""Plugin mixin class for AllocateMixin."""

from django.db.models import Model

from InvenTree.exceptions import log_error
from plugin import PluginMixinEnum


class AllocateMixin:
    """Mixin which allows plugins to customize automatic stock allocation.

    This mixin acts as a "shim" during the auto-allocation of stock items
    against build orders and sales orders. It is called *after* the default
    allocation logic has determined a list of candidate stock items, but
    *before* those items are actually used for allocation.

    This allows a plugin to filter, reorder, or otherwise adjust the list
    of candidate stock items - for example, to implement a custom picking
    strategy, or to exclude certain stock items from automatic allocation.
    """

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'Allocate'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin(PluginMixinEnum.ALLOCATE, True, __class__)

    def filter_build_allocation(
        self, build_line: Model, stock_items: list, **kwargs
    ) -> list:
        """Filter the stock items available for auto-allocation against a build order.

        Arguments:
            build_line: The BuildLine object which is being allocated against
            stock_items: A list of candidate StockItem objects, which have already
                been filtered against the default allocation rules (e.g. in-stock,
                matching part / variant / substitute, location, etc)

        Returns:
            A list of StockItem objects to be used for auto-allocation.

        The default implementation simply returns the provided list of stock items,
        unmodified.
        """
        return stock_items

    def filter_sales_order_allocation(
        self, order_line: Model, stock_items: list, **kwargs
    ) -> list:
        """Filter the stock items available for auto-allocation against a sales order.

        Arguments:
            order_line: The SalesOrderLineItem object which is being allocated against
            stock_items: A list of candidate StockItem objects, which have already
                been filtered against the default allocation rules (e.g. in-stock,
                matching part, location, serialization, etc)

        Returns:
            A list of StockItem objects to be used for auto-allocation.

        The default implementation simply returns the provided list of stock items,
        unmodified.
        """
        return stock_items


def apply_allocate_mixin(
    hook_name: str, line_item, stock_items: list, **kwargs
) -> list:
    """Run the named AllocateMixin hook against every active implementing plugin.

    Arguments:
        hook_name: Name of the AllocateMixin method to call
            (e.g. 'filter_build_allocation' or 'filter_sales_order_allocation')
        line_item: The BuildLine / SalesOrderLineItem being allocated against
        stock_items: The current list of candidate StockItem objects

    Returns:
        The (possibly modified) list of candidate StockItem objects, after being
        passed through every active plugin which implements the AllocateMixin.

    Each active plugin is given the opportunity to filter / reorder the list,
    receiving the output of the previous plugin as its input. If a plugin raises
    an exception, or returns a non-list value, its result is discarded and the
    list is passed unmodified to the next plugin.
    """
    from plugin import registry

    stock_items = list(stock_items)

    for plg in registry.with_mixin(PluginMixinEnum.ALLOCATE):
        try:
            result = getattr(plg, hook_name)(line_item, stock_items, **kwargs)
        except Exception:
            log_error(hook_name, plugin=plg.slug)
            continue

        if result is not None:
            try:
                stock_items = list(result)
            except Exception:
                log_error(hook_name, plugin=plg.slug)

    return stock_items
