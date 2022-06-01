"""Unit tests for the SalesOrder models"""

from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from common.models import InvenTreeSetting
from company.models import Company
from InvenTree import status_codes as status
from order.models import (SalesOrder, SalesOrderAllocation, SalesOrderLineItem,
                          SalesOrderShipment)
from part.models import Part
from stock.models import StockItem


class SalesOrderTest(TestCase):
    """Run tests to ensure that the SalesOrder model is working correctly."""

    def setUp(self):
        """Initial setup for this set of unit tests"""
        # Create a Company to ship the goods to
        self.customer = Company.objects.create(name="ABC Co", description="My customer", is_customer=True)

        # Create a Part to ship
        self.part = Part.objects.create(name='Spanner', salable=True, description='A spanner that I sell')

        # Create some stock!
        self.Sa = StockItem.objects.create(part=self.part, quantity=100)
        self.Sb = StockItem.objects.create(part=self.part, quantity=200)

        # Create a SalesOrder to ship against
        self.order = SalesOrder.objects.create(
            customer=self.customer,
            reference='1234',
            customer_reference='ABC 55555'
        )

        # Create a Shipment against this SalesOrder
        self.shipment = SalesOrderShipment.objects.create(
            order=self.order,
            reference='001',
        )

        # Create a line item
        self.line = SalesOrderLineItem.objects.create(quantity=50, order=self.order, part=self.part)

    def test_overdue(self):
        """Tests for overdue functionality."""
        today = datetime.now().date()

        # By default, order is *not* overdue as the target date is not set
        self.assertFalse(self.order.is_overdue)

        # Set target date in the past
        self.order.target_date = today - timedelta(days=5)
        self.order.save()
        self.assertTrue(self.order.is_overdue)

        # Set target date in the future
        self.order.target_date = today + timedelta(days=5)
        self.order.save()
        self.assertFalse(self.order.is_overdue)

    def test_empty_order(self):
        """Test for an empty order"""
        self.assertEqual(self.line.quantity, 50)
        self.assertEqual(self.line.allocated_quantity(), 0)
        self.assertEqual(self.line.fulfilled_quantity(), 0)
        self.assertFalse(self.line.is_fully_allocated())
        self.assertFalse(self.line.is_over_allocated())

        self.assertTrue(self.order.is_pending)
        self.assertFalse(self.order.is_fully_allocated())

    def test_add_duplicate_line_item(self):
        """Adding a duplicate line item to a SalesOrder is accepted"""

        for ii in range(1, 5):
            SalesOrderLineItem.objects.create(order=self.order, part=self.part, quantity=ii)

    def allocate_stock(self, full=True):
        """Allocate stock to the order"""
        SalesOrderAllocation.objects.create(
            line=self.line,
            shipment=self.shipment,
            item=StockItem.objects.get(pk=self.Sa.pk),
            quantity=25)

        SalesOrderAllocation.objects.create(
            line=self.line,
            shipment=self.shipment,
            item=StockItem.objects.get(pk=self.Sb.pk),
            quantity=25 if full else 20
        )

    def test_allocate_partial(self):
        """Partially allocate stock"""
        self.allocate_stock(False)

        self.assertFalse(self.order.is_fully_allocated())
        self.assertFalse(self.line.is_fully_allocated())
        self.assertEqual(self.line.allocated_quantity(), 45)
        self.assertEqual(self.line.fulfilled_quantity(), 0)

    def test_allocate_full(self):
        """Fully allocate stock"""
        self.allocate_stock(True)

        self.assertTrue(self.order.is_fully_allocated())
        self.assertTrue(self.line.is_fully_allocated())
        self.assertEqual(self.line.allocated_quantity(), 50)

    def test_order_cancel(self):
        """Allocate line items then cancel the order"""
        self.allocate_stock(True)

        self.assertEqual(SalesOrderAllocation.objects.count(), 2)
        self.assertEqual(self.order.status, status.SalesOrderStatus.PENDING)

        self.order.cancel_order()
        self.assertEqual(SalesOrderAllocation.objects.count(), 0)
        self.assertEqual(self.order.status, status.SalesOrderStatus.CANCELLED)

        with self.assertRaises(ValidationError):
            self.order.can_complete(raise_error=True)

        # Now try to ship it - should fail
        result = self.order.complete_order(None)
        self.assertFalse(result)

    def test_complete_order(self):
        """Allocate line items, then ship the order"""
        # Assert some stuff before we run the test
        # Initially there are two stock items
        self.assertEqual(StockItem.objects.count(), 2)

        # Take 25 units from each StockItem
        self.allocate_stock(True)

        self.assertEqual(SalesOrderAllocation.objects.count(), 2)

        # Attempt to complete the order (but shipments are not completed!)
        result = self.order.complete_order(None)

        self.assertFalse(result)

        self.assertIsNone(self.shipment.shipment_date)
        self.assertFalse(self.shipment.is_complete())

        # Mark the shipments as complete
        self.shipment.complete_shipment(None)
        self.assertTrue(self.shipment.is_complete())

        # Now, should be OK to ship
        result = self.order.complete_order(None)

        self.assertTrue(result)

        self.assertEqual(self.order.status, status.SalesOrderStatus.SHIPPED)
        self.assertIsNotNone(self.order.shipment_date)

        # There should now be 4 stock items
        self.assertEqual(StockItem.objects.count(), 4)

        sa = StockItem.objects.get(pk=self.Sa.pk)
        sb = StockItem.objects.get(pk=self.Sb.pk)

        # 25 units subtracted from each of the original items
        self.assertEqual(sa.quantity, 75)
        self.assertEqual(sb.quantity, 175)

        # And 2 items created which are associated with the order
        outputs = StockItem.objects.filter(sales_order=self.order)
        self.assertEqual(outputs.count(), 2)

        for item in outputs.all():
            self.assertEqual(item.quantity, 25)

        self.assertEqual(sa.sales_order, None)
        self.assertEqual(sb.sales_order, None)

        # And the allocations still exist
        self.assertEqual(SalesOrderAllocation.objects.count(), 2)

        self.assertEqual(self.order.status, status.SalesOrderStatus.SHIPPED)

        self.assertTrue(self.order.is_fully_allocated())
        self.assertTrue(self.line.is_fully_allocated())
        self.assertEqual(self.line.fulfilled_quantity(), 50)
        self.assertEqual(self.line.allocated_quantity(), 50)

    def test_default_shipment(self):
        """Test sales order default shipment creation"""
        # Default setting value should be False
        self.assertEqual(False, InvenTreeSetting.get_setting('SALESORDER_DEFAULT_SHIPMENT'))

        # Create an order
        order_1 = SalesOrder.objects.create(
            customer=self.customer,
            reference='1235',
            customer_reference='ABC 55556'
        )

        # Order should have no shipments when setting is False
        self.assertEqual(0, order_1.shipment_count)

        # Update setting to True
        InvenTreeSetting.set_setting('SALESORDER_DEFAULT_SHIPMENT', True, None)
        self.assertEqual(True, InvenTreeSetting.get_setting('SALESORDER_DEFAULT_SHIPMENT'))

        # Create a second order
        order_2 = SalesOrder.objects.create(
            customer=self.customer,
            reference='1236',
            customer_reference='ABC 55557'
        )

        # Order should have one shipment
        self.assertEqual(1, order_2.shipment_count)
        self.assertEqual(1, order_2.pending_shipments().count())

        # Shipment should have default reference of '1'
        self.assertEqual('1', order_2.pending_shipments()[0].reference)
