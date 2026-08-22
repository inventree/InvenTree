"""Background task definitions for the 'pricing' app."""

import structlog

from .models import StockItemCost

logger = structlog.get_logger('inventree')


def update_stock_item_cost(stock_item):
    """Recalculate the cached StockItemCost summary for the given StockItem.

    This is offloaded as a background task after StockItemCostEntry rows are
    bulk-created/updated (see StockItemCostEntryManager.bulk_set_costs) - as
    bulk_create() bypasses the post_save signal that would otherwise trigger
    this recalculation automatically.
    """
    logger.info('Updating stock item cost for %s', stock_item)

    StockItemCost.update_for_stock_item(stock_item)
