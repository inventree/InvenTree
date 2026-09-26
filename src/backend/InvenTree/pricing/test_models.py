"""Unit tests for the pricing app models (StockItemCostEntry / StockItemCost)."""

from django.core.cache import cache
from django.test import TestCase

from djmoney.money import Money

from InvenTree.unit_test import ExchangeRateMixin
from part.models import Part
from stock.models import StockItem

from .models import StockItemCost, StockItemCostEntry
from .status_codes import CostType


class StockItemCostEntryManagerTest(ExchangeRateMixin, TestCase):
    """Tests for the StockItemCostEntryManager helper methods."""

    fixtures = ['category', 'part', 'location', 'stock']

    @classmethod
    def setUpTestData(cls):
        """Initialize test data."""
        super().setUpTestData()

        cls.part = Part.objects.get(pk=1)
        cls.stock_item = StockItem.objects.get(pk=1)
        cls.other_item = StockItem.objects.exclude(pk=cls.stock_item.pk).first()

    def setUp(self):
        """Clear djmoney's exchange-rate cache before each test.

        djmoney caches rate lookups via Django's cache framework (not the DB),
        so it is not reset by TestCase's per-test transaction rollback - a rate
        registered (and looked up) in one test can otherwise leak into a later
        test in the same run that expects no rate to be available.
        """
        super().setUp()
        cache.clear()

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

    def test_add_cost_creates_new_entry(self):
        """add_cost() should create a new entry if none exists, exactly like set_cost()."""
        entry = StockItemCostEntry.objects.add_cost(
            self.stock_item,
            CostType.MATERIAL.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        self.assertEqual(StockItemCostEntry.objects.count(), 1)
        self.assertEqual(entry.min_cost, Money(1, 'USD'))
        self.assertEqual(entry.max_cost, Money(2, 'USD'))

    def test_add_cost_increments_existing_entry(self):
        """add_cost() should add to (not replace) an existing entry's value."""
        StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.MATERIAL.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        entry = StockItemCostEntry.objects.add_cost(
            self.stock_item,
            CostType.MATERIAL.value,
            min_cost=Money(5, 'USD'),
            max_cost=Money(5, 'USD'),
        )

        self.assertEqual(StockItemCostEntry.objects.count(), 1)
        self.assertEqual(entry.min_cost, Money(6, 'USD'))
        self.assertEqual(entry.max_cost, Money(7, 'USD'))

        # The cached summary reflects the incremented value
        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary.min_cost, Money(6, 'USD'))
        self.assertEqual(summary.max_cost, Money(7, 'USD'))

    def test_add_cost_handles_none_values(self):
        """add_cost() should leave an existing value untouched if the added delta is None."""
        StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.MATERIAL.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        entry = StockItemCostEntry.objects.add_cost(
            self.stock_item, CostType.MATERIAL.value, min_cost=Money(5, 'USD')
        )

        self.assertEqual(entry.min_cost, Money(6, 'USD'))
        self.assertEqual(entry.max_cost, Money(2, 'USD'))

    def test_add_cost_converts_mismatched_currency(self):
        """add_cost() should convert an added value into the entry's existing currency."""
        self.generate_exchange_rates()

        StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.MATERIAL.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(1, 'USD'),
        )

        entry = StockItemCostEntry.objects.add_cost(
            self.stock_item,
            CostType.MATERIAL.value,
            min_cost=Money(1.5, 'AUD'),  # 1.5 AUD == 1 USD
            max_cost=Money(1.5, 'AUD'),
        )

        self.assertEqual(str(entry.min_cost_currency), 'USD')
        self.assertAlmostEqual(float(entry.min_cost.amount), 2.0, places=3)
        self.assertAlmostEqual(float(entry.max_cost.amount), 2.0, places=3)

    def test_add_cost_skips_on_missing_exchange_rate(self):
        """If no exchange rate is available, the addition is skipped rather than failing."""
        # Note: generate_exchange_rates() is deliberately not called here
        StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.MATERIAL.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(1, 'USD'),
        )

        entry = StockItemCostEntry.objects.add_cost(
            self.stock_item,
            CostType.MATERIAL.value,
            min_cost=Money(2, 'AUD'),
            max_cost=Money(2, 'AUD'),
        )

        # The existing value is left untouched, rather than raising or being replaced
        self.assertEqual(entry.min_cost, Money(1, 'USD'))
        self.assertEqual(entry.max_cost, Money(1, 'USD'))

    def test_bulk_copy_costs_empty(self):
        """bulk_copy_costs() should be a no-op for an empty input."""
        self.assertEqual(StockItemCostEntry.objects.bulk_copy_costs([]), [])
        self.assertEqual(StockItemCostEntry.objects.count(), 0)

    def test_bulk_copy_costs_source_has_no_costs(self):
        """Copying from a source with no cost data should not create anything."""
        StockItemCostEntry.objects.bulk_copy_costs([(self.stock_item, self.other_item)])

        self.assertEqual(StockItemCostEntry.objects.count(), 0)
        self.assertEqual(StockItemCost.objects.count(), 0)

    def test_bulk_copy_costs_copies_all_entry_types(self):
        """Every cost entry on the source should be duplicated onto the target."""
        StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
            user=None,
            notes='purchased',
            source_data={'po': 123},
        )

        StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.MATERIAL.value,
            min_cost=Money(10, 'USD'),
            max_cost=Money(20, 'USD'),
        )

        StockItemCostEntry.objects.bulk_copy_costs([(self.stock_item, self.other_item)])

        copied = StockItemCostEntry.objects.filter(stock_item=self.other_item)
        self.assertEqual(copied.count(), 2)

        purchase = copied.get(cost_type=CostType.PURCHASE.value)
        self.assertEqual(purchase.min_cost, Money(1, 'USD'))
        self.assertEqual(purchase.max_cost, Money(2, 'USD'))

        # Provenance is carried across too, not just the values
        self.assertEqual(purchase.notes, 'purchased')
        self.assertEqual(purchase.source_data, {'po': 123})

        material = copied.get(cost_type=CostType.MATERIAL.value)
        self.assertEqual(material.min_cost, Money(10, 'USD'))
        self.assertEqual(material.max_cost, Money(20, 'USD'))

        # The source item is left entirely untouched
        self.assertEqual(
            StockItemCostEntry.objects.filter(stock_item=self.stock_item).count(), 2
        )

    def test_bulk_copy_costs_copies_cached_summary(self):
        """The cached StockItemCost summary should be copied across verbatim."""
        StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(3, 'USD'),
            max_cost=Money(4, 'USD'),
        )

        StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.MATERIAL.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(1, 'USD'),
        )

        StockItemCostEntry.objects.bulk_copy_costs([(self.stock_item, self.other_item)])

        source_summary = StockItemCost.objects.get(stock_item=self.stock_item)
        target_summary = StockItemCost.objects.get(stock_item=self.other_item)

        self.assertEqual(target_summary.min_cost, source_summary.min_cost)
        self.assertEqual(target_summary.max_cost, source_summary.max_cost)
        self.assertEqual(target_summary.min_cost, Money(4, 'USD'))
        self.assertEqual(target_summary.max_cost, Money(5, 'USD'))

    def test_bulk_copy_costs_preserves_currency(self):
        """A non-default entry currency should survive the copy unchanged."""
        StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(7, 'AUD'),
            max_cost=Money(9, 'AUD'),
        )

        StockItemCostEntry.objects.bulk_copy_costs([(self.stock_item, self.other_item)])

        copied = StockItemCostEntry.objects.get(
            stock_item=self.other_item, cost_type=CostType.PURCHASE.value
        )

        self.assertEqual(str(copied.min_cost_currency), 'AUD')
        self.assertEqual(copied.min_cost, Money(7, 'AUD'))
        self.assertEqual(copied.max_cost, Money(9, 'AUD'))

    def test_bulk_copy_costs_multiple_pairs(self):
        """Many (source, target) pairs should be handled in a single call."""
        targets = list(
            StockItem.objects.exclude(pk=self.stock_item.pk).order_by('pk')[:3]
        )
        self.assertEqual(len(targets), 3)

        StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(2, 'USD'),
            max_cost=Money(3, 'USD'),
        )

        StockItemCostEntry.objects.bulk_copy_costs([
            (self.stock_item, target) for target in targets
        ])

        for target in targets:
            entry = StockItemCostEntry.objects.get(
                stock_item=target, cost_type=CostType.PURCHASE.value
            )
            self.assertEqual(entry.min_cost, Money(2, 'USD'))
            self.assertEqual(entry.max_cost, Money(3, 'USD'))

            summary = StockItemCost.objects.get(stock_item=target)
            self.assertEqual(summary.min_cost, Money(2, 'USD'))

    def test_bulk_copy_costs_overwrites_existing_target_entry(self):
        """An existing entry of the same type on the target is replaced, not duplicated."""
        StockItemCostEntry.objects.set_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(5, 'USD'),
            max_cost=Money(5, 'USD'),
        )

        StockItemCostEntry.objects.set_cost(
            self.other_item,
            CostType.PURCHASE.value,
            min_cost=Money(99, 'USD'),
            max_cost=Money(99, 'USD'),
        )

        StockItemCostEntry.objects.bulk_copy_costs([(self.stock_item, self.other_item)])

        entries = StockItemCostEntry.objects.filter(stock_item=self.other_item)
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().min_cost, Money(5, 'USD'))

        summary = StockItemCost.objects.get(stock_item=self.other_item)
        self.assertEqual(summary.min_cost, Money(5, 'USD'))
