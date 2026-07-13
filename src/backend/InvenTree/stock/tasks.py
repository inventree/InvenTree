"""Background tasks for the stock app."""

from datetime import datetime, timedelta

import structlog
from opentelemetry import trace

from common.settings import get_global_setting
from InvenTree.tasks import ScheduledTask, scheduled_task

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger('inventree')


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
