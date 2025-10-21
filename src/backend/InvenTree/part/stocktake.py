"""Stock history functionality."""

import structlog
from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money

logger = structlog.get_logger('inventree')


def perform_stocktake() -> None:
    """Generate stock history entries for all active parts."""
    import InvenTree.helpers
    import part.models as part_models
    from common.currency import currency_code_default
    from common.settings import get_global_setting

    if not get_global_setting('STOCKTAKE_ENABLE', False, cache=False):
        logger.info('Stocktake functionality is disabled - skipping')
        return

    exclude_external = get_global_setting(
        'STOCKTAKE_EXCLUDE_EXTERNAL', False, cache=False
    )

    active_parts = part_models.Part.objects.filter(active=True)

    # New history entries to be created
    history_entries = []

    N_BULK_CREATE = 250

    base_currency = currency_code_default()
    today = InvenTree.helpers.current_date()

    logger.info(
        'Creating new stock history entries for %s active parts', active_parts.count()
    )

    for part in active_parts:
        # Is there a recent stock history record for this part?
        if part_models.PartStocktake.objects.filter(
            part=part, date__gte=today
        ).exists():
            continue

        pricing = part.pricing

        # Fetch all 'in stock' items for this part
        stock_items = part.stock_entries(
            in_stock=True, include_external=not exclude_external, include_variants=True
        )

        total_cost_min = Money(0, base_currency)
        total_cost_max = Money(0, base_currency)

        total_quantity = 0
        items_count = 0

        for item in stock_items:
            # Extract cost information

            entry_cost_min = pricing.overall_min or pricing.overall_max
            entry_cost_max = pricing.overall_max or pricing.overall_min

            if item.purchase_price is not None:
                entry_cost_min = item.purchase_price
                entry_cost_max = item.purchase_price

            try:
                entry_cost_min = (
                    convert_money(entry_cost_min, base_currency) * item.quantity
                )
                entry_cost_max = (
                    convert_money(entry_cost_max, base_currency) * item.quantity
                )
            except Exception:
                entry_cost_min = Money(0, base_currency)
                entry_cost_max = Money(0, base_currency)

            # Update total quantities
            items_count += 1
            total_quantity += item.quantity
            total_cost_min += entry_cost_min
            total_cost_max += entry_cost_max

        # Add a new stocktake entry for this part
        history_entries.append(
            part_models.PartStocktake(
                part=part,
                item_count=items_count,
                quantity=total_quantity,
                cost_min=total_cost_min,
                cost_max=total_cost_max,
            )
        )

        # Batch create stock history entries
        if len(history_entries) >= N_BULK_CREATE:
            part_models.PartStocktake.objects.bulk_create(history_entries)
            history_entries = []

    if len(history_entries) > 0:
        # Save any remaining stocktake entries
        part_models.PartStocktake.objects.bulk_create(history_entries)
