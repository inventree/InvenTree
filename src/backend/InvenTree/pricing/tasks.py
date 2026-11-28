"""Background tasks for the 'pricing' app."""

import structlog
from opentelemetry import trace

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger('inventree')


@tracer.start_as_current_span('reconvert_stock_item_costs')
def reconvert_stock_item_costs():
    """Convert any stock item cost entries which are not (yet) converted to the default currency.

    Run after the exchange rates are updated, so that entries which could not previously be
    converted (no exchange rate was available), or which were converted to a previous default
    currency, are included in the cost summary of their stock item.
    """
    from pricing.models import StockItemCostEntry

    count = StockItemCostEntry.objects.reconvert_costs()

    if count:
        logger.info(
            'Converted %s stock item cost entries to the default currency', count
        )
