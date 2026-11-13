"""Helper functions for recording stock item costs from business logic."""

from collections.abc import Iterable
from typing import Any

from django.db import transaction


class StockItemCostRecorder:
    """Collects cost entries for (typically newly created) stock items, and saves them in bulk.

    This is the common pattern for any operation which creates stock items with a known cost
    (receiving a purchase order, completing a build, disassembly, ...):

        costs = StockItemCostRecorder(source=CostSource.PURCHASE_ORDER, user=user)

        for item in new_items:
            costs.add(item, CostType.PURCHASE, cost=unit_cost)

        costs.save()

    On save(), every entry is validated before any are created (all or nothing), the entries
    are bulk created, and the StockItemCost summary for each stock item is created
    (or recalculated) - all within a single transaction.

    Notes:
        - All costs are *per unit* of the stock item - lump sums must be divided down first
          (record the original values in 'source_data')
        - The stock items must already be saved (have a primary key)
        - A missing cost (None) is skipped rather than recorded as zero
    """

    def __init__(self, source: str, user=None):
        """Initialize the recorder.

        Arguments:
            source: Who or what is creating the cost entries (see pricing.models.CostSource)
            user: The user associated with the cost entries (optional)
        """
        self.source = source
        self.user = user
        self.entries: list[dict[str, Any]] = []

    def __len__(self) -> int:
        """Return the number of pending cost entries."""
        return len(self.entries)

    def add(
        self, stock_items, cost_type, cost=None, min_cost=None, max_cost=None, **fields
    ) -> bool:
        """Add a cost entry for one (or many) stock items.

        Arguments:
            stock_items: A saved StockItem, or an iterable of saved StockItems
                (each of which receives an identical cost entry)
            cost_type: The category of the cost (see pricing.status_codes.CostType)
            cost: A single (point) unit cost - shorthand for min_cost = max_cost = cost
            min_cost: Minimum unit cost (Money, or a value in the provided 'currency')
            max_cost: Maximum unit cost (Money, or a value in the provided 'currency')
            **fields: Any other StockItemCostEntry fields (e.g. currency, estimated, source_data, notes)

        Returns:
            True if entries were added, False if no cost was provided (nothing is recorded)

        Raises:
            ValueError: If both 'cost' and 'min_cost' / 'max_cost' are provided,
                or if a stock item has not been saved
        """
        if cost is not None:
            if min_cost is not None or max_cost is not None:
                raise ValueError("Provide either 'cost', or 'min_cost' / 'max_cost'")

            min_cost = max_cost = cost

        if min_cost is None and max_cost is None:
            return False

        if not isinstance(stock_items, Iterable):
            stock_items = [stock_items]

        for stock_item in stock_items:
            if stock_item.pk is None:
                raise ValueError('Cost entries can only be added for saved stock items')

            self.entries.append({
                'source': self.source,
                'user': self.user,
                **fields,
                'stock_item': stock_item,
                'cost_type': cost_type,
                'min_cost': min_cost,
                'max_cost': max_cost,
            })

        return True

    @transaction.atomic
    def save(self) -> list:
        """Create the pending cost entries, and the cost summary for each affected stock item.

        Returns:
            The created StockItemCostEntry objects

        Raises:
            ValidationError: If any of the entries is not valid (no entries are created)
        """
        from pricing.models import StockItemCostEntry

        entries, self.entries = self.entries, []

        return StockItemCostEntry.objects.bulk_create_costs(entries)
