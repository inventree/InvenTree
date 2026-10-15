"""Unit tests for the SampleAllocatePlugin class."""

from build.models import Build, BuildLine, generate_next_build_reference
from company.models import Company
from InvenTree.unit_test import InvenTreeTestCase
from order.models import SalesOrder, SalesOrderLineItem
from part.models import BomItem, Part
from plugin.registry import registry
from stock.models import StockItem


class SampleAllocatePluginTest(InvenTreeTestCase):
    """Tests for the SampleAllocatePlugin class."""

    def enable_plugin(self, en: bool):
        """Enable or disable the SampleAllocatePlugin."""
        registry.set_plugin_state('sampleallocate', en)

    def test_build_auto_allocate(self):
        """The plugin should exclude 'REJECT' batches from build order allocation."""
        assembly = Part.objects.create(name='Assembly', assembly=True)
        component = Part.objects.create(name='Component', component=True)

        BomItem.objects.create(part=assembly, sub_part=component, quantity=5)

        build = Build.objects.create(
            reference=generate_next_build_reference(), part=assembly, quantity=1
        )

        line = BuildLine.objects.get(build=build)

        good_stock = StockItem.objects.create(part=component, quantity=10)
        StockItem.objects.create(part=component, quantity=10, batch='REJECT')

        # With the plugin disabled, either stock item may be selected - not interchangeable
        self.enable_plugin(False)
        build.auto_allocate_stock(interchangeable=False)
        self.assertEqual(line.allocated_quantity(), 0)

        # With the plugin enabled, the 'REJECT' item is filtered out, leaving a single
        # (interchangeable) candidate, which can then be allocated
        self.enable_plugin(True)
        build.auto_allocate_stock(interchangeable=False)

        line.refresh_from_db()
        self.assertEqual(line.allocated_quantity(), 5)
        self.assertEqual(
            list(build.allocated_stock.values_list('stock_item', flat=True)),
            [good_stock.pk],
        )

        self.enable_plugin(False)

    def test_sales_order_auto_allocate(self):
        """The plugin should exclude 'REJECT' batches from sales order allocation."""
        customer = Company.objects.create(name='Customer', is_customer=True)
        part = Part.objects.create(name='Widget', salable=True)

        order = SalesOrder.objects.create(customer=customer)
        line = SalesOrderLineItem.objects.create(order=order, part=part, quantity=5)

        good_stock = StockItem.objects.create(part=part, quantity=10)
        StockItem.objects.create(part=part, quantity=10, batch='REJECT')

        self.enable_plugin(True)
        order.auto_allocate_stock(interchangeable=False)

        self.assertTrue(line.is_fully_allocated())
        self.assertEqual(
            list(order.stock_allocations.values_list('item', flat=True)),
            [good_stock.pk],
        )

        self.enable_plugin(False)
