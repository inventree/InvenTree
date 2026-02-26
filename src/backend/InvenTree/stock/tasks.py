"""Background tasks for the stock app."""

from datetime import datetime, timedelta

import structlog
from opentelemetry import trace

from common.settings import get_global_setting
from InvenTree.tasks import ScheduledTask, offload_task, scheduled_task

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger('inventree')


@tracer.start_as_current_span('rebuild_stock_items')
def rebuild_stock_items():
    """Rebuild the entire StockItem tree structure.

    This may be necessary if the tree structure has become corrupted or inconsistent.
    """
    from InvenTree.exceptions import log_error
    from InvenTree.sentry import report_exception
    from stock.models import StockItem

    logger.info('Rebuilding StockItem tree structure')

    try:
        StockItem.objects.rebuild()
    except Exception as e:
        # This is a critical error, explicitly report to sentry
        report_exception(e)

        log_error('rebuild_stock_items')
        logger.exception('Failed to rebuild StockItem tree: %s', e)


def rebuild_stock_item_tree(tree_id: int, rebuild_on_fail: bool = True) -> bool:
    """Rebuild the stock tree structure.

    Arguments:
        tree_id (int): The ID of the StockItem tree to rebuild.
        rebuild_on_fail (bool): If True, will attempt to rebuild the entire StockItem tree if the partial rebuild fails.

    Returns:
        bool: True if the partial tree rebuild was successful, False otherwise.

    - If the rebuild fails, schedule a rebuild of the entire StockItem tree.
    """
    from InvenTree.exceptions import log_error
    from InvenTree.sentry import report_exception
    from stock.models import StockItem

    if tree_id:
        try:
            StockItem.objects.partial_rebuild(tree_id)
            logger.info('Rebuilt StockItem tree for tree_id: %s', tree_id)
            return True
        except Exception as e:
            # This is a critical error, explicitly report to sentry
            report_exception(e)

            log_error('rebuild_stock_item_tree')
            logger.warning('Failed to rebuild StockItem tree for tree_id: %s', tree_id)
            # If the partial rebuild fails, rebuild the entire tree
            if rebuild_on_fail:
                offload_task(rebuild_stock_items, group='stock')
            return False
    else:
        # No tree_id provided, so rebuild the entire tree
        StockItem.objects.rebuild()
        return True


@tracer.start_as_current_span('delete_old_stock_tracking')
@scheduled_task(ScheduledTask.DAILY)
def delete_old_stock_tracking():
    """Remove old stock tracking entries before a certain date."""
    from stock.models import StockItemTracking

    if not get_global_setting('STOCK_TRACKING_DELETE_OLD_ENTRIES', False):
        return

    delete_n_days = int(get_global_setting('STOCK_TRACKING_DELETE_DAYS', 365))

    threshold = datetime.now() - timedelta(days=delete_n_days)

    old_entries = StockItemTracking.objects.filter(date__lte=threshold)

    if old_entries.exists():
        logger.info(
            'Deleting old stock tracking entries',
            count=old_entries.count(),
            threshold=threshold,
        )
        old_entries.delete()
