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

    def test_create_cost_creates_new_entry(self):
        """create_cost() should create a new entry."""
        self.assertEqual(StockItemCostEntry.objects.count(), 0)

        entry = StockItemCostEntry.objects.create_cost(
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

    def test_create_cost_appends_additional_entry(self):
        """Cost entries are additive - a second entry of the same type is kept alongside the first."""
        first = StockItemCostEntry.objects.create_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        second = StockItemCostEntry.objects.create_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(5, 'USD'),
            max_cost=Money(6, 'USD'),
        )

        # Both entries exist - the first is neither replaced nor updated
        self.assertEqual(StockItemCostEntry.objects.count(), 2)
        self.assertNotEqual(first.pk, second.pk)

        first.refresh_from_db()
        self.assertEqual(first.min_cost, Money(1, 'USD'))
        self.assertEqual(first.max_cost, Money(2, 'USD'))

        # The cached summary is the sum of both entries
        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary.min_cost, Money(6, 'USD'))
        self.assertEqual(summary.max_cost, Money(8, 'USD'))

    def test_create_cost_derives_currency_from_money(self):
        """If no explicit currency is provided, it should be derived from the Money value."""
        entry = StockItemCostEntry.objects.create_cost(
            self.stock_item,
            CostType.MANUAL.value,
            min_cost=Money(1, 'AUD'),
            max_cost=Money(2, 'AUD'),
        )

        self.assertEqual(entry.min_cost_currency, 'AUD')
        self.assertEqual(entry.max_cost_currency, 'AUD')

    def test_bulk_create_costs_empty(self):
        """bulk_create_costs() should be a no-op for an empty list."""
        result = StockItemCostEntry.objects.bulk_create_costs([])
        self.assertEqual(result, [])
        self.assertEqual(StockItemCostEntry.objects.count(), 0)

    def test_bulk_create_costs_creates_across_multiple_items(self):
        """bulk_create_costs() should create entries (and summaries) for multiple stock items in one call."""
        # The summary recalculation is offloaded via batch_offload_tasks(), which
        # defers to the transaction's on_commit hook - capture (and run) it here
        with self.captureOnCommitCallbacks(execute=True):
            StockItemCostEntry.objects.bulk_create_costs([
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

    def test_bulk_create_costs_appends_to_existing_entries(self):
        """bulk_create_costs() adds to whatever the stock item already has, rather than replacing it."""
        StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        with self.captureOnCommitCallbacks(execute=True):
            StockItemCostEntry.objects.bulk_create_costs([
                {
                    'stock_item': self.stock_item,
                    'cost_type': CostType.PURCHASE.value,
                    'min_cost': Money(10, 'USD'),
                    'max_cost': Money(20, 'USD'),
                },
                {
                    'stock_item': self.other_item,
                    'cost_type': CostType.PURCHASE.value,
                    'min_cost': Money(3, 'USD'),
                    'max_cost': Money(4, 'USD'),
                },
            ])

        self.assertEqual(
            StockItemCostEntry.objects.filter(stock_item=self.stock_item).count(), 2
        )

        # The pre-existing entry is untouched, and the summary covers both
        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary.min_cost, Money(11, 'USD'))
        self.assertEqual(summary.max_cost, Money(22, 'USD'))

        summary_other = StockItemCost.objects.get(stock_item=self.other_item)
        self.assertEqual(summary_other.min_cost, Money(3, 'USD'))

    def test_summary_sums_entries_across_cost_types(self):
        """The cached summary is the sum of every entry, whatever its cost type."""
        StockItemCostEntry.objects.create_cost(
            self.stock_item, CostType.PURCHASE.value, min_cost=Money(10, 'USD')
        )
        StockItemCostEntry.objects.create_cost(
            self.stock_item, CostType.LANDED.value, min_cost=Money(2, 'USD')
        )
        StockItemCostEntry.objects.create_cost(
            self.stock_item, CostType.LANDED.value, min_cost=Money(3, 'USD')
        )

        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary.min_cost, Money(15, 'USD'))

    def test_summary_converts_mixed_currencies(self):
        """Entries in different currencies are converted into the default currency before summing."""
        self.generate_exchange_rates()

        StockItemCostEntry.objects.create_cost(
            self.stock_item, CostType.PURCHASE.value, min_cost=Money(1, 'USD')
        )
        StockItemCostEntry.objects.create_cost(
            self.stock_item,
            CostType.LANDED.value,
            min_cost=Money(1.5, 'AUD'),  # 1.5 AUD == 1 USD
        )

        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(str(summary.min_cost_currency), 'USD')
        self.assertAlmostEqual(float(summary.min_cost.amount), 2.0, places=3)

    def test_summary_skips_entry_with_missing_exchange_rate(self):
        """An entry which cannot be converted is skipped, rather than failing the whole summary."""
        # Note: generate_exchange_rates() is deliberately not called here
        StockItemCostEntry.objects.create_cost(
            self.stock_item, CostType.PURCHASE.value, min_cost=Money(1, 'USD')
        )
        StockItemCostEntry.objects.create_cost(
            self.stock_item, CostType.LANDED.value, min_cost=Money(2, 'AUD')
        )

        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary.min_cost, Money(1, 'USD'))

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
        StockItemCostEntry.objects.create_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
            user=None,
            notes='purchased',
            source_data={'po': 123},
        )

        StockItemCostEntry.objects.create_cost(
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
        StockItemCostEntry.objects.create_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(3, 'USD'),
            max_cost=Money(4, 'USD'),
        )

        StockItemCostEntry.objects.create_cost(
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
        StockItemCostEntry.objects.create_cost(
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

        StockItemCostEntry.objects.create_cost(
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

    def test_bulk_copy_costs_appends_to_existing_target_entry(self):
        """Copied entries are added alongside anything the target already has.

        In practice a copy target is always a newly-created stock item with no cost
        data of its own - this simply pins down the additive behaviour if it is not.
        """
        StockItemCostEntry.objects.create_cost(
            self.stock_item,
            CostType.PURCHASE.value,
            min_cost=Money(5, 'USD'),
            max_cost=Money(5, 'USD'),
        )

        StockItemCostEntry.objects.create_cost(
            self.other_item,
            CostType.PURCHASE.value,
            min_cost=Money(99, 'USD'),
            max_cost=Money(99, 'USD'),
        )

        StockItemCostEntry.objects.bulk_copy_costs([(self.stock_item, self.other_item)])

        entries = StockItemCostEntry.objects.filter(stock_item=self.other_item)
        self.assertEqual(entries.count(), 2)
        self.assertEqual(
            sorted(str(entry.min_cost) for entry in entries), ['$5.00', '$99.00']
        )

        # The summary is copied verbatim from the source, as the target is
        # expected to be a split-off copy of it
        summary = StockItemCost.objects.get(stock_item=self.other_item)
        self.assertEqual(summary.min_cost, Money(5, 'USD'))
