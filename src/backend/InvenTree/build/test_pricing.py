"""Unit tests for build order material cost calculation (see build/pricing.py).

Note:
    Consumable and virtual BOM lines are not yet costed here - see the
    "Manufacturing Costs" section of dev/todo/pricing.md for the follow-up plan.
"""

from decimal import Decimal

from django.core.cache import cache

from djmoney.money import Money

from build.models import BuildItem, BuildLine
from common.settings import set_global_setting
from part.models import BomItem, Part
from pricing.models import StockItemCostEntry
from pricing.status_codes import CostType
from stock.models import StockItem

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

    def test_full_multi_output_cycle_with_mixed_costs(self):
        """A single end-to-end build cycle exercising every combination in one run.

        Covers, all at once:
        - measured and estimated contributions mixed together in the same run
        - two different tracked components feeding the same outputs
        - three completed outputs, including a single-unit ("serialized-like") one
        - currency conversion combined with multiple outputs
        - MATERIAL_ESTIMATED at the pooled (whole-build) level, not just per-output

        Component roles (all per single assembly unit, i.e. BOM ratio):
        - sub_part_3 (existing, trackable, 2/unit): tracked, MEASURED, cost in AUD
        - sub_part_4 (new, trackable, 1/unit): tracked, ESTIMATED (price-range fallback)
        - sub_part_1 (existing, untracked, pooled): MEASURED
        - sub_part_2 (existing, untracked, pooled): ESTIMATED (price-range fallback)

        Every quantity below is deliberately chosen as a multiple of either the
        per-output quantity or the total completed quantity (11 = 3 + 7 + 1), so
        the expected per-unit rate is a clean, uniform value on every output.
        """
        self.generate_exchange_rates()

        # A second trackable component, added directly to self.assembly's BOM.
        # The matching BuildLine is created directly, rather than relying on any
        # BOM-change signal to create it for the already-existing build order
        sub_part_4 = Part.objects.create(
            name='Widget D', description='A widget', component=True, trackable=True
        )
        bom_item_4 = BomItem.objects.create(
            part=self.assembly, sub_part=sub_part_4, quantity=1
        )
        BuildLine.objects.create(
            build=self.build, bom_item=bom_item_4, quantity=Decimal(10)
        )
        stock_4_1 = StockItem.objects.create(part=sub_part_4, quantity=1000)

        # A third output - a single-unit output, alongside output_1 (qty 3) and
        # output_2 (qty 7) - total completed quantity is therefore 3 + 7 + 1 = 11
        output_3 = StockItem.objects.create(
            part=self.assembly, quantity=1, is_building=True, build=self.build
        )
        outputs = [self.output_1, self.output_2, output_3]

        # A fresh stock item for the pooled ESTIMATED component, rather than
        # reusing (and inflating the quantity of) a shared class-level fixture item
        stock_2_new = StockItem.objects.create(part=self.sub_part_2, quantity=1000)

        # Tracked, MEASURED: 3 AUD == 2 USD at the registered exchange rate
        StockItemCostEntry.objects.set_cost(
            self.stock_3_1,
            CostType.PURCHASE.value,
            min_cost=Money(3, 'AUD'),
            max_cost=Money(3, 'AUD'),
        )

        # Tracked, ESTIMATED: no recorded cost on stock_4_1 - falls back to this
        self.set_part_price_range(sub_part_4, Money(2, 'USD'), Money(4, 'USD'))

        # Pooled, MEASURED
        StockItemCostEntry.objects.set_cost(
            self.stock_1_2,
            CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(1, 'USD'),
        )

        # Pooled, ESTIMATED: no recorded cost on stock_2_new - falls back to this
        self.set_part_price_range(self.sub_part_2, Money(1, 'USD'), Money(3, 'USD'))

        # Tracked allocations: both sub_part_3 and sub_part_4 feed every output,
        # proportional to its own quantity (2x / 1x per assembly unit respectively)
        for output in outputs:
            self.allocate_stock(
                output,
                {self.stock_3_1: 2 * output.quantity, stock_4_1: 1 * output.quantity},
            )

        # Pooled allocations: sized as multiples of the total completed quantity
        # (11), for a clean per-unit division
        self.allocate_stock(None, {self.stock_1_2: 22})
        self.allocate_stock(None, {stock_2_new: 33})

        for output in outputs:
            self.build.complete_build_output(output, self.user)

        self.build.complete_build(self.user)
        self.build.refresh_from_db()

        # MEASURED: tracked (2/unit x $2 USD-equivalent = $4/unit) + pooled
        # (22 units x $1 / 11 total = $2/unit) = $6/unit, uniform on every output
        #
        # ESTIMATED: tracked (1/unit x $2-$4 range = $2-$4/unit) + pooled
        # (33 units x $1-$3 range / 11 total = $3-$9/unit) = $5-$13/unit, uniform
        for output in outputs:
            material = StockItemCostEntry.objects.get(
                stock_item=output, cost_type=CostType.MATERIAL.value
            )
            self.assertEqual(material.min_cost, Money(6, 'USD'))
            self.assertEqual(material.max_cost, Money(6, 'USD'))

            estimated = StockItemCostEntry.objects.get(
                stock_item=output, cost_type=CostType.MATERIAL_ESTIMATED.value
            )
            self.assertEqual(estimated.min_cost, Money(5, 'USD'))
            self.assertEqual(estimated.max_cost, Money(13, 'USD'))

            # Never a MANUFACTURING (process cost) entry - nothing populates that yet
            self.assertFalse(
                StockItemCostEntry.objects.filter(
                    stock_item=output, cost_type=CostType.MANUFACTURING.value
                ).exists()
            )
