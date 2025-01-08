"""Background tasks for the stock app."""

import structlog

logger = structlog.get_logger('inventree')


def rebuild_stock_item_tree(tree_id=None):
    """Rebuild the stock tree structure.

    The StockItem tree uses the MPTT library to manage the tree structure.
    """
    from stock.models import StockItem

    if tree_id:
        try:
            StockItem.objects.partial_rebuild(tree_id)
        except Exception:
            logger.warning('Failed to rebuild StockItem tree')
            # If the partial rebuild fails, rebuild the entire tree
            StockItem.objects.rebuild()
    else:
        # No tree_id provided, so rebuild the entire tree
        StockItem.objects.rebuild()
