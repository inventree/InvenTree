"""Tests for stock item cost data across the stock item lifecycle.

Covers the business logic which creates, copies or combines stock item cost entries:
splitting, serializing, merging, disassembly and shipping.
"""

from decimal import Decimal

from django.contrib.auth.models import User

from djmoney.money import Money

from company.models import Company
from order.models import (
    SalesOrder,
    SalesOrderAllocation,
    SalesOrderLineItem,
    SalesOrderShipment,
)
from part.models import BomItem, Part
from pricing.models import CostSource, StockItemCost, StockItemCostEntry
from pricing.status_codes import CostType
from pricing.test_stock_cost import StockItemCostTestBase
from stock.models import StockItem


class StockItemCostLifecycleBase(StockItemCostTestBase):
    """Base class with helpers for creating stock items with cost data."""

    def make_item(self, quantity=100, part=None, **kwargs):
        """Create a new stock item."""
        return StockItem.objects.create(
            part=part or self.item.part, quantity=quantity, **kwargs
        )

    def add_cost(self, item, cost_type=CostType.PURCHASE, **kwargs):
        """Add a (manual) cost entry against a stock item."""
        return StockItemCostEntry.objects.create_cost(
            item, cost_type, kwargs.pop('source', CostSource.MANUAL), **kwargs
        )

    def entry_values(self, item) -> list:
        """Return the comparable values of each cost entry for a stock item."""
        return [
            (
                entry.cost_type,
                entry.source,
                entry.currency,
                entry.min_cost,
                entry.max_cost,
                entry.converted_currency,
                entry.converted_min_cost,
                entry.converted_max_cost,
                entry.user_id,
                entry.notes,
                entry.source_data,
            )
            for entry in item.cost_entries.order_by('cost_type', 'pk')
        ]

    def assertSummary(self, item, min_cost, max_cost):
        """Check the cost summary of a stock item."""
        summary = StockItemCost.objects.get(stock_item=item)
        self.assertEqual(summary.currency, 'USD')
        self.assertAlmostEqual(summary.min_cost, Decimal(min_cost), places=4)
        self.assertAlmostEqual(summary.max_cost, Decimal(max_cost), places=4)


class CopyCostTests(StockItemCostLifecycleBase):
    """Cost entries are copied when a stock item is duplicated."""

    def test_copy_costs(self):
        """Entries are copied verbatim (including converted values), and summaries created."""
        self.generate_exchange_rates()

        user = User.objects.create(username='copier')
        source = self.make_item()

        self.add_cost(source, min_cost=Money(10, 'USD'), user=user)
        self.add_cost(
            source,
            CostType.LANDED,
            min_cost=Money(3, 'AUD'),
            max_cost=Money(6, 'AUD'),
            source_data={'invoice': 'INV-1'},
            notes='Freight',
        )

        # The exchange rate changes - copied entries must *not* be reconverted
        self.clear_rate_cache()
        from djmoney.contrib.exchange.models import Rate

        Rate.objects.filter(currency='AUD').update(value=3)

        targets = [self.make_item(), self.make_item()]

        created = StockItemCostEntry.objects.copy_costs([
            (source, targets[0]),
            (source.pk, targets[1].pk),
            (source, source),
        ])

        self.assertEqual(len(created), 4)

        for target in targets:
            self.assertEqual(self.entry_values(target), self.entry_values(source))
            self.assertSummary(target, 12, 14)

        # The source is unchanged (copying onto itself is ignored)
        self.assertEqual(source.cost_entries.count(), 2)

        # Copying from an item without costs removes any (stale) summary
        empty = self.make_item()
        stale = self.make_item()
        StockItemCost.objects.create(stock_item=stale, currency='USD')

        self.assertEqual(StockItemCostEntry.objects.copy_costs([(empty, stale)]), [])
        self.assertFalse(StockItemCost.objects.filter(stock_item=stale).exists())

        with self.assertRaises(ValueError):
            StockItemCostEntry.objects.copy_costs([(source, StockItem())])

    def test_split(self):
        """A split stock item carries the same unit cost."""
        item = self.make_item(quantity=100)
        self.add_cost(item, min_cost=Money(4, 'USD'), max_cost=Money(5, 'USD'))

        new_item = item.splitStock(30, user=None)

        self.assertEqual(new_item.quantity, 30)
        self.assertEqual(self.entry_values(new_item), self.entry_values(item))
        self.assertSummary(new_item, 4, 5)
        self.assertSummary(item, 4, 5)

    def test_serialize(self):
        """Each serialized stock item carries the same unit cost."""
        part = Part.objects.create(
            name='Serialized part', description='A trackable part', trackable=True
        )

        item = self.make_item(quantity=10, part=part)
        self.add_cost(item, min_cost=Money(7, 'USD'))

        items = item.serializeStock(3, ['S1', 'S2', 'S3'], user=None)

        self.assertEqual(len(items), 3)

        for serialized in items:
            self.assertEqual(self.entry_values(serialized), self.entry_values(item))
            self.assertSummary(serialized, 7, 7)

    def test_ship_partial_allocation(self):
        """Stock split off when shipping a sales order carries the same unit cost."""
        part = Part.objects.create(name='Salable', description='Salable', salable=True)
        customer = Company.objects.create(name='Customer', is_customer=True)

        item = self.make_item(quantity=100, part=part)
        self.add_cost(item, min_cost=Money(2, 'USD'))

        order = SalesOrder.objects.create(customer=customer, reference='SO-COST')
        shipment = SalesOrderShipment.objects.create(order=order, reference='1')
        line = SalesOrderLineItem.objects.create(order=order, part=part, quantity=30)

        SalesOrderAllocation.objects.create(
            line=line, shipment=shipment, item=item, quantity=30
        )

        shipment.complete_allocations(SalesOrderAllocation.objects.filter(line=line))

        shipped = StockItem.objects.get(parent=item, sales_order=order)
        self.assertEqual(shipped.quantity, 30)
        self.assertEqual(self.entry_values(shipped), self.entry_values(item))
        self.assertSummary(shipped, 2, 2)

    def test_ship_multiple_sources(self):
        """Each split-off item carries the cost of its *own* source item.

        Regression test: the split-off items are bulk created, and matched back to their
        source items by position - so a mismatch would copy the wrong cost data.
        """
        part = Part.objects.create(name='Salable', description='Salable', salable=True)
        customer = Company.objects.create(name='Customer', is_customer=True)

        items = [self.make_item(quantity=100, part=part) for _ in range(4)]

        for idx, item in enumerate(items):
            self.add_cost(item, min_cost=Money(idx + 1, 'USD'))

        order = SalesOrder.objects.create(customer=customer, reference='SO-COST-2')
        shipment = SalesOrderShipment.objects.create(order=order, reference='1')
        line = SalesOrderLineItem.objects.create(order=order, part=part, quantity=40)

        # Allocated in an order which does not match the stock item (primary key) order
        for item in [items[2], items[0], items[3], items[1]]:
            SalesOrderAllocation.objects.create(
                line=line, shipment=shipment, item=item, quantity=10
            )

        shipment.complete_allocations(SalesOrderAllocation.objects.filter(line=line))

        for idx, item in enumerate(items):
            shipped = StockItem.objects.get(parent=item, sales_order=order)
            self.assertEqual(shipped.quantity, 10)
            self.assertEqual(self.entry_values(shipped), self.entry_values(item))
            self.assertSummary(shipped, idx + 1, idx + 1)


class MergeCostTests(StockItemCostLifecycleBase):
    """Merging stock items combines their cost data."""

    def test_merge_weighted_average(self):
        """One weighted-average entry is created per cost type."""
        a = self.make_item(quantity=10)
        b = self.make_item(quantity=30)
        c = self.make_item(quantity=10)

        self.add_cost(a, min_cost=Money(5, 'USD'))
        self.add_cost(a, CostType.LANDED, min_cost=Money(1, 'USD'))
        self.add_cost(b, min_cost=Money(7, 'USD'), max_cost=Money(9, 'USD'))

        old_entries = list(
            StockItemCostEntry.objects.filter(stock_item__in=[a, b]).values_list(
                'pk', flat=True
            )
        )

        purchase_entries = list(
            StockItemCostEntry.objects.filter(
                stock_item__in=[a, b], cost_type=CostType.PURCHASE
            ).values_list('pk', flat=True)
        )

        # Note: the merged items are deleted (losing their primary key)
        merged_pks = sorted([a.pk, b.pk])

        # 'c' has no cost data (unknown cost) - excluded from the weighting
        a.merge_stock_items([b, c])

        a.refresh_from_db()
        self.assertEqual(a.quantity, 50)

        entries = {entry.cost_type: entry for entry in a.cost_entries.all()}
        self.assertEqual(set(entries.keys()), {CostType.PURCHASE, CostType.LANDED})

        # PURCHASE: (5 x 10 + 7 x 30) / 40 = 6.5 ; (5 x 10 + 9 x 30) / 40 = 8
        purchase = entries[CostType.PURCHASE]
        self.assertEqual(purchase.source, CostSource.MERGE)
        self.assertEqual(purchase.currency, 'USD')
        self.assertEqual(purchase.min_cost, Decimal('6.5'))
        self.assertEqual(purchase.max_cost, Decimal('8'))

        self.assertEqual(purchase.source_data['merged_items'], merged_pks)
        # The original entries are recorded against the merged entry
        self.assertEqual(
            sorted(e['pk'] for e in purchase.source_data['entries']),
            sorted(purchase_entries),
        )

        # LANDED: (1 x 10 + 0 x 30) / 40 = 0.25
        landed = entries[CostType.LANDED]
        self.assertEqual(landed.min_cost, Decimal('0.25'))
        self.assertEqual(landed.max_cost, Decimal('0.25'))

        self.assertSummary(a, '6.75', '8.25')

        # The original entries no longer exist
        self.assertFalse(StockItemCostEntry.objects.filter(pk__in=old_entries).exists())

    def test_merge_mixed_currencies(self):
        """Mixed currencies are averaged using the converted values."""
        self.generate_exchange_rates()

        a = self.make_item(quantity=10)
        b = self.make_item(quantity=10)
        c = self.make_item(quantity=20)

        self.add_cost(a, min_cost=Money(10, 'USD'))

        # 15 AUD = 10 USD
        self.add_cost(b, min_cost=Money(15, 'AUD'))

        # No exchange rate available - excluded (contributes zero)
        self.add_cost(c, min_cost=Money(1000, 'JPY'))

        a.merge_stock_items([b, c])

        entry = a.cost_entries.get()
        self.assertEqual(entry.currency, 'USD')

        # (10 x 10 + 10 x 10 + 0 x 20) / 40 = 5
        self.assertEqual(entry.min_cost, Decimal(5))
        self.assertEqual(len(entry.source_data['excluded_entries']), 1)

        self.assertSummary(a, 5, 5)

    def test_merge_single_currency(self):
        """A cost type with a single (non default) currency is averaged in that currency."""
        a = self.make_item(quantity=10)
        b = self.make_item(quantity=30)

        # No exchange rates are required
        self.add_cost(a, min_cost=Money(4, 'AUD'))
        self.add_cost(b, min_cost=Money(8, 'AUD'))

        a.merge_stock_items([b])

        entry = a.cost_entries.get()
        self.assertEqual(entry.currency, 'AUD')
        self.assertEqual(entry.min_cost, Decimal(7))

    def test_merge_target_only(self):
        """If only the target has cost data, its entries are left untouched."""
        a = self.make_item(quantity=10)
        b = self.make_item(quantity=10)

        entry = self.add_cost(a, min_cost=Money(5, 'USD'))

        a.merge_stock_items([b])

        self.assertEqual(list(a.cost_entries.all()), [entry])
        self.assertSummary(a, 5, 5)


class DisassemblyCostTests(StockItemCostLifecycleBase):
    """Cost entries recorded when disassembling a stock item.

    - Explicit (per line) unit costs are recorded as provided
    - The remaining cost of the assembly is allocated across the other lines,
      weighted by part pricing - only if pricing is available for *every* such line
    - All entries use the MATERIAL cost type
    """

    def setUp(self):
        """Create an assembly with two components."""
        super().setUp()

        self.assembly = Part.objects.create(
            name='Assembly', description='An assembly', assembly=True
        )

        self.components = [
            Part.objects.create(name=f'Component {idx}', description='A component')
            for idx in range(2)
        ]

        self.bom_items = [
            BomItem.objects.create(part=self.assembly, sub_part=component, quantity=1)
            for component in self.components
        ]

    def set_pricing(self, part, min_price, max_price=None):
        """Set the (overall) pricing data for a part."""
        pricing = part.pricing
        pricing.override_min = Money(min_price, 'USD')
        pricing.override_max = Money(max_price or min_price, 'USD')
        pricing.save()

        self.assertEqual(part.pricing.overall_min.amount, min_price)

    def disassemble(self, item, lines, user=None):
        """Disassemble 2 units of the provided item."""
        return item.disassemble(
            2, [{'bom_item': bom_item, **line} for bom_item, line in lines], user=user
        )

    def assertDecimals(self, values: list, expected: list):
        """Check a list of (string) decimal values recorded in the source data."""
        self.assertEqual(
            [Decimal(value) for value in values], [Decimal(e) for e in expected]
        )

    def assertEntry(self, item, min_cost, max_cost, allocation):
        """Check the (single) disassembly cost entry for a component."""
        entry = item.cost_entries.get()

        self.assertEqual(entry.cost_type, CostType.MATERIAL)
        self.assertEqual(entry.source, CostSource.DISASSEMBLY)
        self.assertAlmostEqual(float(entry.min_cost), float(min_cost), places=5)
        self.assertAlmostEqual(float(entry.max_cost), float(max_cost), places=5)
        self.assertEqual(entry.source_data['allocation'], allocation)

        # The cost summary of the component matches its (single) entry
        if entry.currency == 'USD':
            self.assertSummary(item, Decimal(str(min_cost)), Decimal(str(max_cost)))

        return entry

    def assertNoCost(self, item):
        """Check that a component has no cost entries (and no cost summary)."""
        self.assertFalse(item.cost_entries.exists())
        self.assertFalse(StockItemCost.objects.filter(stock_item=item).exists())

    def test_allocated_from_pricing(self):
        """The cost of the disassembled units is apportioned using part pricing."""
        item = self.make_item(quantity=5, part=self.assembly)
        self.add_cost(item, min_cost=Money(10, 'USD'), max_cost=Money(12, 'USD'))

        # Weights: 4 x 1 = 4 and 6 x 2 = 12 (1/4 and 3/4 of the total)
        self.set_pricing(self.components[0], 1)
        self.set_pricing(self.components[1], 1, 3)

        components = self.disassemble(
            item,
            [
                (self.bom_items[0], {'quantity': 4}),
                (self.bom_items[1], {'quantity': 6}),
            ],
        )

        # Total cost = 2 x 10 (min) / 2 x 12 (max)
        entry = self.assertEntry(components[0], 20 / 4 / 4, 24 / 4 / 4, 'pricing')
        self.assertEntry(components[1], 20 * 3 / 4 / 6, 24 * 3 / 4 / 6, 'pricing')

        self.assertEqual(entry.source_data['stock_item'], item.pk)
        self.assertDecimals(entry.source_data['allocated_cost'], [20, 24])

        # The cost range (estimate) of the assembly carries through
        self.assertSummary(components[0], '1.25', '1.5')

    def test_missing_pricing(self):
        """No cost is allocated unless pricing is available for every line."""
        item = self.make_item(quantity=5, part=self.assembly)
        self.add_cost(item, min_cost=Money(10, 'USD'))

        # Pricing for only one of the two components
        self.set_pricing(self.components[0], 1)

        components = self.disassemble(
            item,
            [
                (self.bom_items[0], {'quantity': 4}),
                (self.bom_items[1], {'quantity': 6}),
            ],
        )

        for component in components:
            self.assertNoCost(component)

    def test_no_cost_data(self):
        """Components of an assembly without cost data have no cost entries."""
        item = self.make_item(quantity=5, part=self.assembly)
        self.set_pricing(self.components[0], 1)

        components = self.disassemble(item, [(self.bom_items[0], {'quantity': 4})])

        self.assertNoCost(components[0])

    def test_explicit_costs(self):
        """Explicit unit costs are recorded (no 'pricing' role is required)."""
        item = self.make_item(quantity=5, part=self.assembly)
        self.add_cost(item, min_cost=Money(10, 'USD'))

        lines = [
            (self.bom_items[0], {'quantity': 4, 'unit_cost': Money(3, 'USD')}),
            (self.bom_items[1], {'quantity': 6, 'unit_cost': Money(1, 'USD')}),
        ]

        # Explicit costs do not require any pricing data
        components = self.disassemble(item, lines)

        for component, cost in zip(components, [3, 1], strict=True):
            self.assertEntry(component, cost, cost, 'explicit')

        # No 'pricing' role is required - the cost is part of the stock operation
        user = User.objects.create(username='no-pricing')

        item = self.make_item(quantity=5, part=self.assembly)

        components = self.disassemble(item, lines, user=user)

        for component, cost in zip(components, [3, 1], strict=True):
            entry = self.assertEntry(component, cost, cost, 'explicit')
            self.assertEqual(entry.user, user)

    def test_explicit_and_allocated(self):
        """The remaining cost (after explicit costs) is allocated across the other lines."""
        self.generate_exchange_rates()

        item = self.make_item(quantity=5, part=self.assembly)
        self.add_cost(item, min_cost=Money(10, 'USD'), max_cost=Money(12, 'USD'))

        # Only the line *without* an explicit cost requires pricing data
        self.set_pricing(self.components[1], 1)

        # 4 x 1.5 AUD = 6 AUD = 4 USD
        components = self.disassemble(
            item,
            [
                (self.bom_items[0], {'quantity': 4, 'unit_cost': Money('1.5', 'AUD')}),
                (self.bom_items[1], {'quantity': 6}),
            ],
        )

        entry = components[0].cost_entries.get()
        self.assertEqual(entry.currency, 'AUD')
        self.assertEqual(entry.min_cost, Decimal('1.5'))

        # 1.5 AUD = 1 USD
        self.assertSummary(components[0], 1, 1)

        # Remaining cost: 20 - 4 = 16 (min) / 24 - 4 = 20 (max), across 6 units
        entry = self.assertEntry(components[1], 16 / 6, 20 / 6, 'pricing')
        self.assertDecimals([entry.source_data['explicit_cost']], [4])
        self.assertDecimals(entry.source_data['allocated_cost'], [16, 20])

    def test_explicit_without_pricing(self):
        """Lines without an explicit cost (or pricing data) have no cost recorded."""
        item = self.make_item(quantity=5, part=self.assembly)
        self.add_cost(item, min_cost=Money(10, 'USD'))

        components = self.disassemble(
            item,
            [
                (self.bom_items[0], {'quantity': 4, 'unit_cost': Money(1, 'USD')}),
                (self.bom_items[1], {'quantity': 6}),
            ],
        )

        self.assertEntry(components[0], 1, 1, 'explicit')
        self.assertNoCost(components[1])

    def test_explicit_exceeds_cost(self):
        """Nothing is allocated if the explicit costs exceed the cost of the assembly."""
        item = self.make_item(quantity=5, part=self.assembly)
        self.add_cost(item, min_cost=Money(10, 'USD'))
        self.set_pricing(self.components[1], 1)

        # 4 x 5 = 20 USD (the entire cost of the disassembled units)
        components = self.disassemble(
            item,
            [
                (self.bom_items[0], {'quantity': 4, 'unit_cost': Money(5, 'USD')}),
                (self.bom_items[1], {'quantity': 6}),
            ],
        )

        self.assertEntry(components[0], 5, 5, 'explicit')
        self.assertNoCost(components[1])

    def test_installed_items_deducted(self):
        """The cost of installed items is deducted from the allocated cost."""
        item = self.make_item(quantity=2, part=self.assembly)
        self.add_cost(item, min_cost=Money(10, 'USD'))

        self.set_pricing(self.components[0], 1)
        self.set_pricing(self.components[1], 1)

        # An installed item (2 x 3 USD) for the first component
        installed = self.make_item(quantity=2, part=self.components[0])
        installed.belongs_to = item
        installed.save()
        self.add_cost(installed, min_cost=Money(3, 'USD'))

        # 2 x 10 USD - 2 x 3 USD = 14 USD remaining
        components = item.disassemble(
            2,
            [
                {'bom_item': self.bom_items[0], 'quantity': 4},
                {'bom_item': self.bom_items[1], 'quantity': 2},
            ],
            user=None,
        )

        installed.refresh_from_db()
        self.assertIsNone(installed.belongs_to)

        # The installed item keeps its own cost
        entry = installed.cost_entries.get()
        self.assertEqual(entry.cost_type, CostType.PURCHASE)
        self.assertEqual(entry.min_cost, 3)
        self.assertSummary(installed, 3, 3)

        # Two new items (2 units each, equal pricing) share the remaining 14 USD
        created = [c for c in components if c.pk != installed.pk]
        self.assertEqual(len(created), 2)

        for component in created:
            self.assertEqual(component.quantity, 2)
            entry = self.assertEntry(component, '3.5', '3.5', 'pricing')
            self.assertDecimals(entry.source_data['installed_cost'], [6, 6])

    def test_installed_items_exceed_cost(self):
        """Nothing is allocated if installed items account for the entire cost."""
        item = self.make_item(quantity=1, part=self.assembly)
        self.add_cost(item, min_cost=Money(5, 'USD'))
        self.set_pricing(self.components[1], 1)

        installed = self.make_item(quantity=1, part=self.components[0])
        installed.belongs_to = item
        installed.save()
        self.add_cost(installed, min_cost=Money(8, 'USD'))

        components = item.disassemble(
            1,
            [
                {'bom_item': self.bom_items[0], 'quantity': 1},
                {'bom_item': self.bom_items[1], 'quantity': 1},
            ],
            user=None,
        )

        created = [c for c in components if c.pk != installed.pk]
        self.assertEqual(len(created), 1)
        self.assertNoCost(created[0])


class StocktakeCostTests(StockItemCostLifecycleBase):
    """Stocktake values stock items using their recorded unit cost."""

    def test_stocktake_value(self):
        """The stock value is calculated from the cost summary of each stock item."""
        from common.settings import set_global_setting
        from part.models import PartStocktake
        from part.stocktake import perform_stocktake

        set_global_setting('STOCKTAKE_ENABLE', True)
        self.generate_exchange_rates()

        part = Part.objects.create(name='Valued part', description='A part')

        a = self.make_item(quantity=10, part=part)
        self.add_cost(a, min_cost=Money(2, 'USD'), max_cost=Money(3, 'USD'))

        # 15 AUD = 10 USD
        b = self.make_item(quantity=5, part=part)
        self.add_cost(b, min_cost=Money(15, 'AUD'))

        # No recorded cost (and no part pricing) - no contribution
        self.make_item(quantity=4, part=part)

        perform_stocktake(part_id=part.pk)

        stocktake = PartStocktake.objects.get(part=part)

        self.assertEqual(stocktake.item_count, 3)
        self.assertEqual(stocktake.quantity, 19)

        # min: 10 x 2 + 5 x 10 = 70 ; max: 10 x 3 + 5 x 10 = 80
        self.assertAlmostEqual(stocktake.cost_min.amount, Decimal(70), places=4)
        self.assertAlmostEqual(stocktake.cost_max.amount, Decimal(80), places=4)
        self.assertEqual(str(stocktake.cost_min.currency), 'USD')
