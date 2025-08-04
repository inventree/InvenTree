"""Stocktake report functionality."""

from django.contrib.auth.models import User

import structlog
from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money

import common.currency
import common.models

logger = structlog.get_logger('inventree')


def perform_stocktake(target, user: User, note: str = '', commit=True, **kwargs):
    """Perform stocktake action on a single part.

    Arguments:
        target: A single Part model instance
        user: User who requested this stocktake
        note: Optional note to attach to the stocktake
        commit: If True (default) save the result to the database

    kwargs:
        exclude_external: If True, exclude stock items in external locations (default = False)
        location: Optional StockLocation to filter results for generated report

    Returns:
        PartStocktake: A new PartStocktake model instance (for the specified Part)

    Note that while we record a *total stocktake* for the Part instance which gets saved to the database,
    the user may have requested a stocktake limited to a particular location.

    In this case, the stocktake *report* will be limited to the specified location.
    """
    import part.models

    # Determine which locations are "valid" for the generated report
    location = kwargs.get('location')
    locations = location.get_descendants(include_self=True) if location else []

    # Grab all "available" stock items for the Part
    # We do not include variant stock when performing a stocktake,
    # otherwise the stocktake entries will be duplicated
    stock_entries = target.stock_entries(in_stock=True, include_variants=False)

    exclude_external = kwargs.get('exclude_external', False)

    if exclude_external:
        stock_entries = stock_entries.exclude(location__external=True)

    # Cache min/max pricing information for this Part
    pricing = target.pricing

    if not pricing.is_valid:
        # If pricing is not valid, let's update
        logger.info('Pricing not valid for %s - updating', target)
        pricing.update_pricing(cascade=False)
        pricing.refresh_from_db()

    base_currency = common.currency.currency_code_default()

    # Keep track of total quantity and cost for this part
    total_quantity = 0
    total_cost_min = Money(0, base_currency)
    total_cost_max = Money(0, base_currency)

    # Separately, keep track of stock quantity and value within the specified location
    location_item_count = 0
    location_quantity = 0
    location_cost_min = Money(0, base_currency)
    location_cost_max = Money(0, base_currency)

    for entry in stock_entries:
        entry_cost_min = None
        entry_cost_max = None

        # Update price range values
        if entry.purchase_price:
            entry_cost_min = entry.purchase_price
            entry_cost_max = entry.purchase_price

        else:
            # If no purchase price is available, fall back to the part pricing data
            entry_cost_min = pricing.overall_min or pricing.overall_max
            entry_cost_max = pricing.overall_max or pricing.overall_min

        # Convert to base currency
        try:
            entry_cost_min = (
                convert_money(entry_cost_min, base_currency) * entry.quantity
            )
            entry_cost_max = (
                convert_money(entry_cost_max, base_currency) * entry.quantity
            )
        except Exception:
            entry_cost_min = Money(0, base_currency)
            entry_cost_max = Money(0, base_currency)

        # Update total cost values
        total_quantity += entry.quantity
        total_cost_min += entry_cost_min
        total_cost_max += entry_cost_max

        # Test if this stock item is within the specified location
        if location and entry.location not in locations:
            continue

        # Update location cost values
        location_item_count += 1
        location_quantity += entry.quantity
        location_cost_min += entry_cost_min
        location_cost_max += entry_cost_max

    # Construct PartStocktake instance
    # Note that we use the *total* values for the PartStocktake instance
    instance = part.models.PartStocktake(
        part=target,
        item_count=stock_entries.count(),
        quantity=total_quantity,
        cost_min=total_cost_min,
        cost_max=total_cost_max,
        note=note,
        user=user,
    )

    if commit:
        instance.save()

    # Add location-specific data to the instance
    instance.location_item_count = location_item_count
    instance.location_quantity = location_quantity
    instance.location_cost_min = location_cost_min
    instance.location_cost_max = location_cost_max

    return instance
