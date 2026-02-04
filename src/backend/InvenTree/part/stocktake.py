"""Stock history functionality."""

from typing import Optional

from django.db.models import QuerySet

import structlog
from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money

import common.models

logger = structlog.get_logger('inventree')


def perform_stocktake(
    parts: Optional[QuerySet] = None,
    category_id: Optional[int] = None,
    location_id: Optional[int] = None,
    exclude_external: Optional[bool] = None,
    generate_entry: bool = True,
    report_output: Optional[common.models.DataOutput] = None,
) -> None:
    """Capture a snapshot of stock-on-hand and stock value.

    Arguments:
        parts: Optional queryset of parts to perform stocktake on. If not provided, all active parts will be processed.
        category_id: Optional category ID to use to filter parts
        location_id: Optional location ID to use to filter stock items
        exclude_external: If True, exclude external stock items from the stocktake
        generate_entry: If True, create stocktake entries in the database
        report_output: Optional output destination for the stocktake report (e.g. for download)

    The default implementation creates stocktake entries for all active parts,
    and writes these stocktake entries to the database.

    Alternatively, the scope of the stocktake can be limited by providing a queryset of parts,
    or by providing a category ID or location ID to filter the parts/stock items.
    """
    import InvenTree.helpers
    import part.models as part_models
    import stock.models as stock_models
    from common.currency import currency_code_default
    from common.settings import get_global_setting

    if not get_global_setting('STOCKTAKE_ENABLE', False, cache=False):
        logger.info('Stocktake functionality is disabled - skipping')
        return

    # If exclude_external is not provided, use global setting
    if exclude_external is None:
        exclude_external = get_global_setting(
            'STOCKTAKE_EXCLUDE_EXTERNAL', False, cache=False
        )

    if parts is None:
        parts = part_models.Part.objects.filter(active=True)

    # Filter part queryset by category, if provided
    if category_id is not None:
        # Filter parts by category (including subcategories)
        try:
            category = part_models.PartCategory.objects.get(id=category_id)
            parts = parts.filter(
                category__in=category.get_descendants(include_self=True)
            )
        except (ValueError, part_models.PartCategory.DoesNotExist):
            pass

    # Fetch location if provided
    if location_id is not None:
        try:
            location = stock_models.StockLocation.objects.get(id=location_id)
        except (ValueError, stock_models.StockLocation.DoesNotExist):
            location = None
    else:
        location = None

    if location is not None:
        # Location limited, so we will disable saving of stocktake entries
        generate_entry = False

    # New history entries to be created
    history_entries = []

    base_currency = currency_code_default()
    today = InvenTree.helpers.current_date()

    logger.info('Creating new stock history entries for %s parts', parts.count())

    if report_output:
        # Initialize progress on the report output
        report_output.total = parts.count()
        report_output.progress = 0
        report_output.complete = False
        report_output.save()

    for part in parts:
        # Is there a recent stock history record for this part?
        if (
            generate_entry
            and part_models.PartStocktake.objects.filter(
                part=part, date__gte=today
            ).exists()
        ):
            continue

        pricing = part.pricing

        # Fetch all 'in stock' items for this part
        stock_items = part.stock_entries(
            location=location,
            in_stock=True,
            include_external=not exclude_external,
            include_variants=True,
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

    if generate_entry:
        # Bulk-create PartStocktake entries
        part_models.PartStocktake.objects.bulk_create(history_entries)

    if report_output:
        # Save report data, and mark as complete
        ...
