"""Unit tests for the pricing app models (StockItemCostEntry / StockItemCost)."""

from django.test import TestCase

from djmoney.money import Money

from part.models import Part
from stock.models import StockItem

from .models import StockItemCost, StockItemCostEntry
from .status_codes import CostType


class StockItemCostEntryManagerTest(TestCase):
    """Tests for the StockItemCostEntryManager helper methods."""

    fixtures = ['category', 'part', 'location', 'stock']

    @classmethod
    def setUpTestData(cls):
        """Initialize test data."""
        super().setUpTestData()

        cls.part = Part.objects.get(pk=1)
        cls.stock_item = StockItem.objects.get(pk=1)
        cls.other_item = StockItem.objects.exclude(pk=cls.stock_item.pk).first()

    def test_set_cost_creates_new_entry(self):
        """set_cost() should create a new entry if none exists."""
        self.assertEqual(StockItemCostEntry.objects.count(), 0)

        entry = StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        self.assertEqual(StockItemCostEntry.objects.count(), 1)
        self.assertEqual(entry.stock_item, self.stock_item)
        self.assertEqual(entry.cost_type, CostType.PURCHASE.value)
        self.assertEqual(entry.min_cost, Money(1, 'USD'))
        self.assertEqual(entry.max_cost, Money(2, 'USD'))

        # The cached summary should have been created via the normal signal
        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary.min_cost, Money(1, 'USD'))
        self.assertEqual(summary.max_cost, Money(2, 'USD'))

    def test_set_cost_updates_existing_entry(self):
        """set_cost() should update the existing entry for a (stock_item, cost_type) pair."""
        first = StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        second = StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(5, 'USD'),
            max_cost=Money(6, 'USD'),
        )

        # No new entry should have been created
        self.assertEqual(StockItemCostEntry.objects.count(), 1)
        self.assertEqual(first.pk, second.pk)

        first.refresh_from_db()
        self.assertEqual(first.min_cost, Money(5, 'USD'))
        self.assertEqual(first.max_cost, Money(6, 'USD'))

        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary.min_cost, Money(5, 'USD'))
        self.assertEqual(summary.max_cost, Money(6, 'USD'))

    def test_set_cost_derives_currency_from_money(self):
        """If no explicit currency is provided, it should be derived from the Money value."""
        entry = StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.MANUAL.value,
            min_cost=Money(1, 'AUD'),
            max_cost=Money(2, 'AUD'),
        )

        self.assertEqual(entry.min_cost_currency, 'AUD')
        self.assertEqual(entry.max_cost_currency, 'AUD')

    def test_bulk_set_costs_empty(self):
        """bulk_set_costs() should be a no-op for an empty list."""
        result = StockItemCostEntry.objects.bulk_set_costs([])
        self.assertEqual(result, [])
        self.assertEqual(StockItemCostEntry.objects.count(), 0)

    def test_bulk_set_costs_creates_across_multiple_items(self):
        """bulk_set_costs() should create entries (and summaries) for multiple stock items in one call."""
        # The summary recalculation is offloaded via batch_offload_tasks(), which
        # defers to the transaction's on_commit hook - capture (and run) it here
        with self.captureOnCommitCallbacks(execute=True):
            StockItemCostEntry.objects.bulk_set_costs([
                {
                    'stock_item': self.stock_item,
                    'cost_type': CostType.PURCHASE.value,
                    'min_cost': Money(1, 'USD'),
                    'max_cost': Money(2, 'USD'),
                },
                {
                    'stock_item': self.other_item,
                    'cost_type': CostType.PURCHASE.value,
                    'min_cost': Money(3, 'USD'),
                    'max_cost': Money(4, 'USD'),
                },
            ])

        self.assertEqual(StockItemCostEntry.objects.count(), 2)

        summary_1 = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary_1.min_cost, Money(1, 'USD'))
        self.assertEqual(summary_1.max_cost, Money(2, 'USD'))

        summary_2 = StockItemCost.objects.get(stock_item=self.other_item)
        self.assertEqual(summary_2.min_cost, Money(3, 'USD'))
        self.assertEqual(summary_2.max_cost, Money(4, 'USD'))

    def test_bulk_set_costs_updates_existing_entries(self):
        """bulk_set_costs() should update (not duplicate) entries that already exist."""
        StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        with self.captureOnCommitCallbacks(execute=True):
            StockItemCostEntry.objects.bulk_set_costs([
                {
                    'stock_item': self.stock_item,
                    'cost_type': CostType.PURCHASE.value,
                    'min_cost': Money(10, 'USD'),
                    'max_cost': Money(20, 'USD'),
                }
            ])

        self.assertEqual(StockItemCostEntry.objects.count(), 1)

        entry = StockItemCostEntry.objects.get(
            stock_item=self.stock_item, cost_type=CostType.PURCHASE.value
        )
        self.assertEqual(entry.min_cost, Money(10, 'USD'))
        self.assertEqual(entry.max_cost, Money(20, 'USD'))

        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary.min_cost, Money(10, 'USD'))
        self.assertEqual(summary.max_cost, Money(20, 'USD'))

    def test_bulk_set_costs_mixed_create_and_update(self):
        """A single bulk_set_costs() call can create some entries and update others at once."""
        StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        with self.captureOnCommitCallbacks(execute=True):
            StockItemCostEntry.objects.bulk_set_costs([
                {
                    'stock_item': self.stock_item,
                    'cost_type': CostType.PURCHASE.value,
                    'min_cost': Money(9, 'USD'),
                    'max_cost': Money(9, 'USD'),
                },
                {
                    'stock_item': self.other_item,
                    'cost_type': CostType.PURCHASE.value,
                    'min_cost': Money(3, 'USD'),
                    'max_cost': Money(4, 'USD'),
                },
            ])

        self.assertEqual(StockItemCostEntry.objects.count(), 2)

        updated = StockItemCostEntry.objects.get(
            stock_item=self.stock_item, cost_type=CostType.PURCHASE.value
        )
        self.assertEqual(updated.min_cost, Money(9, 'USD'))

        created = StockItemCostEntry.objects.get(
            stock_item=self.other_item, cost_type=CostType.PURCHASE.value
        )
        self.assertEqual(created.min_cost, Money(3, 'USD'))

        # Summaries should be recalculated for both affected stock items
        summary_updated = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary_updated.min_cost, Money(9, 'USD'))

        summary_created = StockItemCost.objects.get(stock_item=self.other_item)
        self.assertEqual(summary_created.min_cost, Money(3, 'USD'))
