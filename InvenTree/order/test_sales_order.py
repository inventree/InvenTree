# -*- coding: utf-8 -*-

from django.test import TestCase

from django.core.exceptions import ValidationError

from datetime import datetime, timedelta

from company.models import Company

from InvenTree import status_codes as status

from order.models import SalesOrder, SalesOrderLineItem, SalesOrderShipment, SalesOrderAllocation

from part.models import Part

from stock.models import StockItem


class SalesOrderTest(TestCase):
    """
    Run tests to ensure that the SalesOrder model is working correctly.

    """

    def setUp(self):

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

        # Create a line item
        self.line = SalesOrderLineItem.objects.create(quantity=50, order=self.order, part=self.part)

    def test_overdue(self):
        """
        Tests for overdue functionality
        """

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
        self.assertEqual(self.line.quantity, 50)
        self.assertEqual(self.line.allocated_quantity(), 0)
        self.assertEqual(self.line.fulfilled_quantity(), 0)
        self.assertFalse(self.line.is_fully_allocated())
        self.assertFalse(self.line.is_over_allocated())

        self.assertTrue(self.order.is_pending)
        self.assertFalse(self.order.is_fully_allocated())

    def test_add_duplicate_line_item(self):
        # Adding a duplicate line item to a SalesOrder is accepted

        for ii in range(1, 5):
            SalesOrderLineItem.objects.create(order=self.order, part=self.part, quantity=ii)

    def allocate_stock(self, full=True):

        # Allocate stock to the order
        SalesOrderAllocation.objects.create(
            line=self.line,
            item=StockItem.objects.get(pk=self.Sa.pk),
            quantity=25)

        SalesOrderAllocation.objects.create(
            line=self.line,
            item=StockItem.objects.get(pk=self.Sb.pk),
            quantity=25 if full else 20
        )

    def test_allocate_partial(self):
        # Partially allocate stock
        self.allocate_stock(False)

        self.assertFalse(self.order.is_fully_allocated())
        self.assertFalse(self.line.is_fully_allocated())
        self.assertEqual(self.line.allocated_quantity(), 45)
        self.assertEqual(self.line.fulfilled_quantity(), 0)

    def test_allocate_full(self):
        # Fully allocate stock
        self.allocate_stock(True)

        self.assertTrue(self.order.is_fully_allocated())
        self.assertTrue(self.line.is_fully_allocated())
        self.assertEqual(self.line.allocated_quantity(), 50)

    def test_order_cancel(self):
        # Allocate line items then cancel the order

        self.allocate_stock(True)

        self.assertEqual(SalesOrderAllocation.objects.count(), 2)
        self.assertEqual(self.order.status, status.SalesOrderStatus.PENDING)

        self.order.cancel_order()
        self.assertEqual(SalesOrderAllocation.objects.count(), 0)
        self.assertEqual(self.order.status, status.SalesOrderStatus.CANCELLED)

        # Now try to ship it - should fail
        with self.assertRaises(ValidationError):
            self.order.ship_order(None)

    def test_ship_order(self):
        # Allocate line items, then ship the order

        # Assert some stuff before we run the test
        # Initially there are two stock items
        self.assertEqual(StockItem.objects.count(), 2)

        # Take 25 units from each StockItem
        self.allocate_stock(True)

        self.assertEqual(SalesOrderAllocation.objects.count(), 2)

        self.order.ship_order(None)

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

        # And no allocations
        self.assertEqual(SalesOrderAllocation.objects.count(), 0)

        self.assertEqual(self.order.status, status.SalesOrderStatus.SHIPPED)

        self.assertTrue(self.order.is_fully_allocated())
        self.assertTrue(self.line.is_fully_allocated())
        self.assertEqual(self.line.fulfilled_quantity(), 50)
        self.assertEqual(self.line.allocated_quantity(), 0)
