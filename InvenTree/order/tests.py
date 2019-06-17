from django.test import TestCase
import django.core.exceptions as django_exceptions

from part.models import Part
from .models import PurchaseOrder, PurchaseOrderLineItem
from stock.models import StockLocation

from InvenTree.status_codes import OrderStatus


class OrderTest(TestCase):
    """
    Tests to ensure that the order models are functioning correctly.
    """

    fixtures = [
        'company',
        'supplier_part',
        'category',
        'part',
        'location',
        'stock',
        'order'
    ]

    def test_basics(self):

        order = PurchaseOrder.objects.get(pk=1)

        self.assertEqual(order.get_absolute_url(), '/order/purchase-order/1/')

        self.assertEqual(str(order), 'PO 1')
        
        line = PurchaseOrderLineItem.objects.get(pk=1)

        self.assertEqual(str(line), "100 x ACME0001 from ACME (for PO 1)")

    def test_on_order(self):
        """ There should be 3 separate items on order for the M2x4 LPHS part """

        part = Part.objects.get(name='M2x4 LPHS')

        open_orders = []

        for supplier in part.supplier_parts.all():
            open_orders += supplier.open_orders()

        self.assertEqual(len(open_orders), 3)

        # Test the total on-order quantity
        self.assertEqual(part.on_order, 400)

    def test_receive(self):

        part = Part.objects.get(name='M2x4 LPHS')

        # Receive some items
        line = PurchaseOrderLineItem.objects.get(id=1)

        order = line.order
        loc = StockLocation.objects.get(id=1)

        # There should be two lines against this order
        self.assertEqual(len(order.pending_line_items()), 2)

        # Should fail, as order is 'PENDING' not 'PLACED"
        self.assertEqual(order.status, OrderStatus.PENDING)

        with self.assertRaises(django_exceptions.ValidationError):
            order.receive_line_item(line, loc, 50, user=None)

        order.place_order()

        self.assertEqual(order.status, OrderStatus.PLACED)

        order.receive_line_item(line, loc, 50, user=None)

        self.assertEqual(part.on_order, 350)

        # Try to order some invalid things
        with self.assertRaises(django_exceptions.ValidationError):
            order.receive_line_item(line, loc, -10, user=None)

        with self.assertRaises(django_exceptions.ValidationError):
            order.receive_line_item(line, loc, 'not a number', user=None)
        
        # Receive the rest of the items
        order.receive_line_item(line, loc, 50, user=None)

        line = PurchaseOrderLineItem.objects.get(id=2)
        order.receive_line_item(line, loc, 2 * line.quantity, user=None)

        self.assertEqual(part.on_order, 100)
        self.assertEqual(order.status, OrderStatus.COMPLETE)
