"""Background tasks for the stock app."""

import structlog
from opentelemetry import trace

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger('inventree')


@tracer.start_as_current_span('rebuild_stock_item_tree')
def rebuild_stock_item_tree(tree_id=None):
    """Rebuild the stock tree structure.

    The StockItem tree uses the MPTT library to manage the tree structure.
    """
    from InvenTree.exceptions import log_error
    from stock.models import StockItem

    if tree_id:
        try:
            StockItem.objects.partial_rebuild(tree_id)
        except Exception:
            log_error('rebuild_stock_item_tree')
            logger.warning('Failed to rebuild StockItem tree')
            # If the partial rebuild fails, rebuild the entire tree
            StockItem.objects.rebuild()
    else:
        # No tree_id provided, so rebuild the entire tree
        StockItem.objects.rebuild()
