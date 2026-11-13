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
                entry.estimated,
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

    def assertSummary(self, item, min_cost, max_cost, estimated=False):
        """Check the cost summary of a stock item."""
        summary = StockItemCost.objects.get(stock_item=item)
        self.assertEqual(summary.currency, 'USD')
        self.assertAlmostEqual(summary.min_cost, Decimal(min_cost), places=4)
        self.assertAlmostEqual(summary.max_cost, Decimal(max_cost), places=4)
        self.assertEqual(summary.estimated, estimated)


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
            estimated=True,
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
            self.assertSummary(target, 12, 14, estimated=True)

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
        self.assertFalse(purchase.estimated)

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

        # No exchange rate available - excluded (contributes zero), and marked as estimated
        self.add_cost(c, min_cost=Money(1000, 'JPY'))

        a.merge_stock_items([b, c])

        entry = a.cost_entries.get()
        self.assertEqual(entry.currency, 'USD')

        # (10 x 10 + 10 x 10 + 0 x 20) / 40 = 5
        self.assertEqual(entry.min_cost, Decimal(5))
        self.assertTrue(entry.estimated)
        self.assertEqual(len(entry.source_data['excluded_entries']), 1)

        self.assertSummary(a, 5, 5, estimated=True)

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
    """Disassembled components receive a share of the cost of the assembly."""

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

    def disassemble(self, item, lines, user=None):
        """Disassemble 2 units of the provided item."""
        return item.disassemble(
            2, [{'bom_item': bom_item, **line} for bom_item, line in lines], user=user
        )

    def test_allocated_from_summary(self):
        """The cost of the disassembled units is apportioned across the components."""
        item = self.make_item(quantity=5, part=self.assembly)

        self.add_cost(item, min_cost=Money(10, 'USD'), max_cost=Money(12, 'USD'))
        self.add_cost(item, CostType.LANDED, min_cost=Money(0, 'USD'), estimated=True)

        components = self.disassemble(
            item,
            [
                (self.bom_items[0], {'quantity': 4}),
                (self.bom_items[1], {'quantity': 6}),
            ],
        )

        self.assertEqual(len(components), 2)

        # No part pricing data - the cost is split evenly per unit:
        # total cost = 2 x 10 (min) / 2 x 12 (max) across 10 units
        for component in components:
            entry = component.cost_entries.get()

            self.assertEqual(entry.cost_type, CostType.PURCHASE)
            self.assertEqual(entry.source, CostSource.DISASSEMBLY)
            self.assertEqual(entry.min_cost, Decimal(2))
            self.assertEqual(entry.max_cost, Decimal('2.4'))

            # The assembly cost includes an estimate
            self.assertTrue(entry.estimated)
            self.assertEqual(entry.source_data['stock_item'], item.pk)
            self.assertEqual(entry.source_data['allocation'], 'even')

            self.assertSummary(component, 2, '2.4', estimated=True)

    def test_no_cost_data(self):
        """Components of an assembly without cost data have no cost entries."""
        item = self.make_item(quantity=5, part=self.assembly)

        components = self.disassemble(item, [(self.bom_items[0], {'quantity': 4})])

        self.assertFalse(components[0].cost_entries.exists())

    def test_explicit_prices(self):
        """Explicit prices are recorded (only for users with permission to add costs)."""
        item = self.make_item(quantity=5, part=self.assembly)
        self.add_cost(item, min_cost=Money(10, 'USD'))

        lines = [
            (self.bom_items[0], {'quantity': 4, 'purchase_price': Money(3, 'USD')}),
            (self.bom_items[1], {'quantity': 6, 'purchase_price': Money(1, 'USD')}),
        ]

        components = self.disassemble(item, lines)

        for component, cost in zip(components, [3, 1], strict=True):
            entry = component.cost_entries.get()
            self.assertEqual(entry.min_cost, cost)
            self.assertEqual(entry.source_data['allocation'], 'explicit')

        # No 'pricing' role is required - the cost is part of the stock operation
        user = User.objects.create(username='no-pricing')

        item = self.make_item(quantity=5, part=self.assembly)
        self.add_cost(item, min_cost=Money(10, 'USD'))

        components = self.disassemble(item, lines, user=user)

        for component, cost in zip(components, [3, 1], strict=True):
            entry = component.cost_entries.get()
            self.assertEqual(entry.min_cost, cost)
            self.assertEqual(entry.user, user)


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
