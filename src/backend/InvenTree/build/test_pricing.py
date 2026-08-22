"""Unit tests for build order material cost calculation (see build/pricing.py).

Note:
    Consumable and virtual BOM lines are not yet costed here - see the
    "Manufacturing Costs" section of dev/todo/pricing.md for the follow-up plan.
"""

from django.core.cache import cache

from djmoney.money import Money

from build.models import BuildItem, BuildLine
from common.settings import set_global_setting
from pricing.models import StockItemCostEntry
from pricing.status_codes import CostType

from .test_build import BuildTestBase


class BuildMaterialCostTest(BuildTestBase):
    """Tests for automatic material cost allocation on build order completion.

    Reuses the BOM fixture from BuildTestBase:
        - 5 x sub_part_1 (non-trackable) per assembly -> untracked allocation
        - 3 x sub_part_2 (non-trackable, optional) per assembly -> untracked allocation
        - 2 x sub_part_3 (trackable) per assembly -> tracked (per-output) allocation

    self.build has quantity=10, split into output_1 (qty 3) and output_2 (qty 7).
    """

    def setUp(self):
        """Ensure a consistent default currency, and move the build into production."""
        super().setUp()
        set_global_setting('INVENTREE_DEFAULT_CURRENCY', 'USD')
        self.build.issue_build()

        # djmoney caches rate lookups via Django's cache framework (not the DB),
        # so it is not reset by TestCase's per-test transaction rollback - a rate
        # registered (and looked up) in one test can otherwise leak into a later
        # test in the same run that expects no rate to be available
        cache.clear()

    def allocate_stock(self, output, allocations):
        """Create BuildItem allocations against self.build for the given output.

        Arguments:
            output: StockItem object (or None, for an untracked/pooled allocation)
            allocations: Map of {StockItem: quantity}
        """
        items_to_create = []

        for item, quantity in allocations.items():
            line = BuildLine.objects.filter(
                build=self.build, bom_item__sub_part=item.part
            ).first()

            items_to_create.append(
                BuildItem(
                    build_line=line,
                    stock_item=item,
                    quantity=quantity,
                    install_into=output,
                )
            )

        BuildItem.objects.bulk_create(items_to_create)

    def set_part_price_range(self, part, min_cost, max_cost):
        """Set a manual price override for a part, so its pricing.overall_min/max is deterministic."""
        pricing = part.pricing
        pricing.override_min = min_cost
        pricing.override_max = max_cost
        pricing.save()
        return part.pricing

    def test_tracked_measured_cost(self):
        """A tracked allocation with a recorded cost produces a measured MATERIAL entry."""
        StockItemCostEntry.objects.set_cost(
            self.stock_3_1,
            CostType.PURCHASE.value,
            min_cost=Money(2, 'USD'),
            max_cost=Money(3, 'USD'),
        )

        # 2 x sub_part_3 per assembly, 3 assemblies in output_1 -> 6 units allocated
        self.allocate_stock(self.output_1, {self.stock_3_1: 6})
        self.build.complete_build_output(self.output_1, self.user)

        entry = StockItemCostEntry.objects.get(
            stock_item=self.output_1, cost_type=CostType.MATERIAL.value
        )

        # (6 units * cost) / 3 output units
        self.assertEqual(entry.min_cost, Money(4, 'USD'))
        self.assertEqual(entry.max_cost, Money(6, 'USD'))

        # No estimated entry, since the allocated stock had a recorded cost
        self.assertFalse(
            StockItemCostEntry.objects.filter(
                stock_item=self.output_1, cost_type=CostType.MATERIAL_ESTIMATED.value
            ).exists()
        )

    def test_tracked_estimated_cost(self):
        """A tracked allocation with no recorded cost falls back to the part's price range."""
        self.set_part_price_range(self.sub_part_3, Money(1, 'USD'), Money(5, 'USD'))

        self.allocate_stock(self.output_1, {self.stock_3_1: 6})
        self.build.complete_build_output(self.output_1, self.user)

        entry = StockItemCostEntry.objects.get(
            stock_item=self.output_1, cost_type=CostType.MATERIAL_ESTIMATED.value
        )

        self.assertEqual(entry.min_cost, Money(2, 'USD'))  # (6 * 1) / 3
        self.assertEqual(entry.max_cost, Money(10, 'USD'))  # (6 * 5) / 3

        self.assertFalse(
            StockItemCostEntry.objects.filter(
                stock_item=self.output_1, cost_type=CostType.MATERIAL.value
            ).exists()
        )

    def test_no_cost_data_skips_contribution(self):
        """No recorded cost, and no part pricing available - no cost entry is created."""
        self.allocate_stock(self.output_1, {self.stock_3_1: 6})
        self.build.complete_build_output(self.output_1, self.user)

        self.assertFalse(
            StockItemCostEntry.objects.filter(stock_item=self.output_1).exists()
        )

    def test_pooled_cost_apportioned_across_outputs(self):
        """Untracked allocation cost is applied evenly, per-unit, to every completed output."""
        StockItemCostEntry.objects.set_cost(
            self.stock_1_2,
            CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(1, 'USD'),
        )

        # 5 x sub_part_1 per assembly, 10 assemblies total -> 50 units allocated (untracked)
        self.allocate_stock(None, {self.stock_1_2: 50})

        self.build.complete_build_output(self.output_1, self.user)
        self.build.complete_build_output(self.output_2, self.user)
        self.build.complete_build(self.user)
        self.build.refresh_from_db()

        # (50 units * 1 USD) / 10 total completed units = 5 USD/unit, applied to every output
        for output in (self.output_1, self.output_2):
            entry = StockItemCostEntry.objects.get(
                stock_item=output, cost_type=CostType.MATERIAL.value
            )
            self.assertEqual(entry.min_cost, Money(5, 'USD'))
            self.assertEqual(entry.max_cost, Money(5, 'USD'))

    def test_pooled_cost_is_additive_to_tracked_cost(self):
        """The pooled (whole-build) pass adds to, rather than replaces, the per-output tracked cost."""
        StockItemCostEntry.objects.set_cost(
            self.stock_3_1,
            CostType.PURCHASE.value,
            min_cost=Money(2, 'USD'),
            max_cost=Money(2, 'USD'),
        )
        StockItemCostEntry.objects.set_cost(
            self.stock_1_2,
            CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(1, 'USD'),
        )

        # Tracked: fully allocate sub_part_3 into both outputs (+4 USD/unit measured, each)
        self.allocate_stock(self.output_1, {self.stock_3_1: 6})
        self.allocate_stock(self.output_2, {self.stock_3_1: 14})

        # Untracked/pooled: fully allocate sub_part_1 (+5 USD/unit measured, once the build completes)
        self.allocate_stock(None, {self.stock_1_2: 50})

        self.build.complete_build_output(self.output_1, self.user)
        self.build.complete_build_output(self.output_2, self.user)
        self.build.complete_build(self.user)
        self.build.refresh_from_db()

        for output in (self.output_1, self.output_2):
            entry = StockItemCostEntry.objects.get(
                stock_item=output, cost_type=CostType.MATERIAL.value
            )
            # 4 (tracked) + 5 (pooled) = 9 USD/unit
            self.assertEqual(entry.min_cost, Money(9, 'USD'))
            self.assertEqual(entry.max_cost, Money(9, 'USD'))

    def test_currency_conversion(self):
        """Allocated stock cost in a non-default currency is converted before summing."""
        self.generate_exchange_rates()

        StockItemCostEntry.objects.set_cost(
            self.stock_3_1,
            CostType.PURCHASE.value,
            min_cost=Money(2, 'AUD'),
            max_cost=Money(2, 'AUD'),
        )

        self.allocate_stock(self.output_1, {self.stock_3_1: 6})
        self.build.complete_build_output(self.output_1, self.user)

        entry = StockItemCostEntry.objects.get(
            stock_item=self.output_1, cost_type=CostType.MATERIAL.value
        )

        self.assertEqual(str(entry.min_cost_currency), 'USD')
        # (6 units * (2 AUD / 1.5)) / 3 output units
        self.assertAlmostEqual(float(entry.min_cost.amount), 2.6667, places=3)
        self.assertAlmostEqual(float(entry.max_cost.amount), 2.6667, places=3)

    def test_missing_exchange_rate_skips_contribution(self):
        """If no exchange rate is available, that contribution is skipped, not zeroed."""
        # Note: generate_exchange_rates() is deliberately not called here
        StockItemCostEntry.objects.set_cost(
            self.stock_3_1,
            CostType.PURCHASE.value,
            min_cost=Money(2, 'AUD'),
            max_cost=Money(2, 'AUD'),
        )

        self.allocate_stock(self.output_1, {self.stock_3_1: 6})
        self.build.complete_build_output(self.output_1, self.user)

        self.assertFalse(
            StockItemCostEntry.objects.filter(stock_item=self.output_1).exists()
        )
