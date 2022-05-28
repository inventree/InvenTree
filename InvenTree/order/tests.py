from datetime import datetime, timedelta

import django.core.exceptions as django_exceptions
from django.test import TestCase

from company.models import SupplierPart
from InvenTree.status_codes import PurchaseOrderStatus
from part.models import Part
from stock.models import StockLocation

from .models import PurchaseOrder, PurchaseOrderLineItem


class OrderTest(TestCase):
    """Tests to ensure that the order models are functioning correctly."""

    fixtures = [
        'company',
        'supplier_part',
        'price_breaks',
        'category',
        'part',
        'location',
        'stock',
        'order'
    ]

    def test_basics(self):
        """Basic tests e.g. repr functions etc"""
        order = PurchaseOrder.objects.get(pk=1)

        self.assertEqual(order.get_absolute_url(), '/order/purchase-order/1/')

        self.assertEqual(str(order), 'PO0001 - ACME')

        line = PurchaseOrderLineItem.objects.get(pk=1)

        self.assertEqual(str(line), "100 x ACME0001 from ACME (for PO0001 - ACME)")

    def test_overdue(self):
        """Test overdue status functionality"""
        today = datetime.now().date()

        order = PurchaseOrder.objects.get(pk=1)
        self.assertFalse(order.is_overdue)

        order.target_date = today - timedelta(days=5)
        order.save()
        self.assertTrue(order.is_overdue)

        order.target_date = today + timedelta(days=1)
        order.save()
        self.assertFalse(order.is_overdue)

    def test_on_order(self):
        """There should be 3 separate items on order for the M2x4 LPHS part"""
        part = Part.objects.get(name='M2x4 LPHS')

        open_orders = []

        for supplier in part.supplier_parts.all():
            open_orders += supplier.open_orders()

        self.assertEqual(len(open_orders), 4)

        # Test the total on-order quantity
        self.assertEqual(part.on_order, 1400)

    def test_add_items(self):
        """Test functions for adding line items to an order"""
        order = PurchaseOrder.objects.get(pk=1)

        self.assertEqual(order.status, PurchaseOrderStatus.PENDING)
        self.assertEqual(order.lines.count(), 4)

        sku = SupplierPart.objects.get(SKU='ACME-WIDGET')
        part = sku.part

        # Try to order some invalid things
        with self.assertRaises(django_exceptions.ValidationError):
            order.add_line_item(sku, -999)

        with self.assertRaises(django_exceptions.ValidationError):
            order.add_line_item(sku, 'not a number')

        # Order the part
        self.assertEqual(part.on_order, 0)

        order.add_line_item(sku, 100)

        self.assertEqual(part.on_order, 100)
        self.assertEqual(order.lines.count(), 5)

        # Order the same part again (it should be merged)
        order.add_line_item(sku, 50)
        self.assertEqual(order.lines.count(), 5)
        self.assertEqual(part.on_order, 150)

        # Try to order a supplier part from the wrong supplier
        sku = SupplierPart.objects.get(SKU='ZERG-WIDGET')

        with self.assertRaises(django_exceptions.ValidationError):
            order.add_line_item(sku, 99)

    def test_pricing(self):
        """Test functions for adding line items to an order including price-breaks"""
        order = PurchaseOrder.objects.get(pk=7)

        self.assertEqual(order.status, PurchaseOrderStatus.PENDING)
        self.assertEqual(order.lines.count(), 0)

        sku = SupplierPart.objects.get(SKU='ZERGM312')
        part = sku.part

        # Order the part
        self.assertEqual(part.on_order, 0)

        # Order 25 with manually set high value
        pp = sku.get_price(25)
        order.add_line_item(sku, 25, purchase_price=pp)
        self.assertEqual(part.on_order, 25)
        self.assertEqual(order.lines.count(), 1)
        self.assertEqual(order.lines.first().purchase_price.amount, 200)

        # Add a few, now the pricebreak should adjust although wrong price given
        order.add_line_item(sku, 10, purchase_price=sku.get_price(25))
        self.assertEqual(part.on_order, 35)
        self.assertEqual(order.lines.count(), 1)
        self.assertEqual(order.lines.first().purchase_price.amount, 8)

        # Order the same part again (it should be merged)
        order.add_line_item(sku, 100, purchase_price=sku.get_price(100))
        self.assertEqual(order.lines.count(), 1)
        self.assertEqual(part.on_order, 135)
        self.assertEqual(order.lines.first().purchase_price.amount, 1.25)

    def test_receive(self):
        """Test order receiving functions"""
        part = Part.objects.get(name='M2x4 LPHS')

        # Receive some items
        line = PurchaseOrderLineItem.objects.get(id=1)

        order = line.order
        loc = StockLocation.objects.get(id=1)

        # There should be two lines against this order
        self.assertEqual(len(order.pending_line_items()), 4)

        # Should fail, as order is 'PENDING' not 'PLACED"
        self.assertEqual(order.status, PurchaseOrderStatus.PENDING)

        with self.assertRaises(django_exceptions.ValidationError):
            order.receive_line_item(line, loc, 50, user=None)

        order.place_order()

        self.assertEqual(order.status, PurchaseOrderStatus.PLACED)

        order.receive_line_item(line, loc, 50, user=None)

        self.assertEqual(line.remaining(), 50)

        self.assertEqual(part.on_order, 1350)

        # Try to order some invalid things
        with self.assertRaises(django_exceptions.ValidationError):
            order.receive_line_item(line, loc, -10, user=None)

        with self.assertRaises(django_exceptions.ValidationError):
            order.receive_line_item(line, loc, 'not a number', user=None)

        # Receive the rest of the items
        order.receive_line_item(line, loc, 50, user=None)

        line = PurchaseOrderLineItem.objects.get(id=2)

        order.receive_line_item(line, loc, 500, user=None)

        self.assertEqual(part.on_order, 800)
        self.assertEqual(order.status, PurchaseOrderStatus.PLACED)

        for line in order.pending_line_items():
            order.receive_line_item(line, loc, line.quantity, user=None)

        self.assertEqual(order.status, PurchaseOrderStatus.COMPLETE)
