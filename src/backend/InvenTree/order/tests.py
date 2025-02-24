"""Various unit tests for order models."""

from datetime import datetime, timedelta
from decimal import Decimal

import django.core.exceptions as django_exceptions
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from djmoney.money import Money

import common.models
import order.tasks
from common.settings import get_global_setting, set_global_setting
from company.models import Company, SupplierPart
from InvenTree.unit_test import ExchangeRateMixin
from order.status_codes import PurchaseOrderStatus
from part.models import Part
from stock.models import StockItem, StockLocation
from users.models import Owner

from .models import PurchaseOrder, PurchaseOrderExtraLine, PurchaseOrderLineItem


class OrderTest(TestCase, ExchangeRateMixin):
    """Tests to ensure that the order models are functioning correctly."""

    fixtures = [
        'company',
        'supplier_part',
        'price_breaks',
        'category',
        'part',
        'location',
        'stock',
        'order',
        'users',
    ]

    def test_basics(self):
        """Basic tests e.g. repr functions etc."""
        for pk in range(1, 8):
            order = PurchaseOrder.objects.get(pk=pk)
            self.assertEqual(
                order.get_absolute_url(), f'/platform/purchasing/purchase-order/{pk}'
            )

            self.assertEqual(order.reference, f'PO-{pk:04d}')

        line = PurchaseOrderLineItem.objects.get(pk=1)
        self.assertEqual(str(line), '100 x ACME0001 - PO-0001 - ACME')

    def test_rebuild_reference(self):
        """Test that the reference_int field is correctly updated when the model is saved."""
        order = PurchaseOrder.objects.get(pk=1)
        order.save()
        self.assertEqual(order.reference_int, 1)

        order.reference = '12345XYZ'
        order.save()
        self.assertEqual(order.reference_int, 12345)

    def test_locking(self):
        """Test the (auto)locking functionality of the (Purchase)Order model."""
        order = PurchaseOrder.objects.get(pk=1)

        order.status = PurchaseOrderStatus.PENDING
        order.save()
        self.assertFalse(order.check_locked())

        order.status = PurchaseOrderStatus.COMPLETE
        order.save()
        self.assertFalse(order.check_locked())

        order.add_line_item(SupplierPart.objects.get(pk=100), 100)
        last_line = order.lines.last()
        self.assertEqual(last_line.quantity, 100)

        # Reset
        order.status = PurchaseOrderStatus.PENDING
        order.save()

        # Turn on auto-locking
        set_global_setting(PurchaseOrder.LOCK_SETTING, True)
        # still not locked
        self.assertFalse(order.check_locked())

        order.status = PurchaseOrderStatus.COMPLETE
        # the instance is locked, the db instance is not
        self.assertFalse(order.check_locked(True))
        self.assertTrue(order.check_locked())
        order.save()
        # now everything is locked
        self.assertTrue(order.check_locked(True))
        self.assertTrue(order.check_locked())

        # No editing allowed
        with self.assertRaises(django_exceptions.ValidationError):
            order.description = 'test1'
            order.save()
        order.refresh_from_db()
        self.assertEqual(order.description, 'Ordering some screws')

        # Also no adding of line items
        with self.assertRaises(django_exceptions.ValidationError):
            order.add_line_item(SupplierPart.objects.get(pk=100), 100)
        # or deleting
        with self.assertRaises(django_exceptions.ValidationError):
            last_line.delete()

        # Still can create a completed item
        PurchaseOrder.objects.create(
            supplier=Company.objects.get(pk=1),
            reference='PO-99999',
            status=PurchaseOrderStatus.COMPLETE,
        )

        # No editing (except status ;-) ) allowed
        order.status = PurchaseOrderStatus.PENDING
        order.save()

        # Now it is a free for all again
        order.description = 'test2'
        order.save()

        order.refresh_from_db()
        self.assertEqual(order.description, 'test2')

    def test_overdue(self):
        """Test overdue status functionality."""
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
        """There should be 3 separate items on order for the M2x4 LPHS part."""
        part = Part.objects.get(name='M2x4 LPHS')

        open_orders = []

        for supplier in part.supplier_parts.all():
            open_orders += supplier.open_orders()

        self.assertEqual(len(open_orders), 4)

        # Test the total on-order quantity
        self.assertEqual(part.on_order, 1400)

    def test_add_items(self):
        """Test functions for adding line items to an order."""
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
        """Test functions for adding line items to an order including price-breaks."""
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
        """Test order receiving functions."""
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

        self.assertEqual(part.on_order, 1300)

        line = PurchaseOrderLineItem.objects.get(id=2)

        in_stock = part.total_stock

        order.receive_line_item(line, loc, 500, user=None)

        # Check that the part stock quantity has increased by the correct amount
        self.assertEqual(part.total_stock, in_stock + 500)

        self.assertEqual(part.on_order, 1100)
        self.assertEqual(order.status, PurchaseOrderStatus.PLACED)

        for line in order.pending_line_items():
            order.receive_line_item(line, loc, line.quantity, user=None)

        self.assertEqual(order.status, PurchaseOrderStatus.COMPLETE)

    def test_receive_pack_size(self):
        """Test receiving orders from suppliers with different pack_size values."""
        prt = Part.objects.get(pk=1)
        sup = Company.objects.get(pk=1)

        # Create a new supplier part with larger pack size
        sp_1 = SupplierPart.objects.create(
            part=prt, supplier=sup, SKU='SKUx10', pack_quantity='10'
        )

        # Create a new supplier part with smaller pack size
        sp_2 = SupplierPart.objects.create(
            part=prt, supplier=sup, SKU='SKUx0.1', pack_quantity='0.1'
        )

        # Record values before we start
        on_order = prt.on_order
        in_stock = prt.total_stock

        n = PurchaseOrder.objects.count()

        # Create a new PurchaseOrder
        po = PurchaseOrder.objects.create(
            supplier=sup, reference=f'PO-{n + 1}', description='Some PO'
        )

        # Add line items

        # 3 x 10 = 30
        line_1 = PurchaseOrderLineItem.objects.create(
            order=po,
            part=sp_1,
            quantity=3,
            purchase_price=Money(1000, 'USD'),  # "Unit price" should be $100USD
        )

        # 13 x 0.1 = 1.3
        line_2 = PurchaseOrderLineItem.objects.create(
            order=po,
            part=sp_2,
            quantity=13,
            purchase_price=Money(10, 'USD'),  # "Unit price" should be $100USD
        )

        po.place_order()

        # The 'on_order' quantity should have been increased by 31.3
        self.assertEqual(prt.on_order, round(on_order + Decimal(31.3), 1))

        loc = StockLocation.objects.get(id=1)

        # Receive 1x item against line_1
        po.receive_line_item(line_1, loc, 1, user=None)

        # Receive 5x item against line_2
        po.receive_line_item(line_2, loc, 5, user=None)

        # Check that the line items have been updated correctly
        self.assertEqual(line_1.quantity, 3)
        self.assertEqual(line_1.received, 1)
        self.assertEqual(line_1.remaining(), 2)

        self.assertEqual(line_2.quantity, 13)
        self.assertEqual(line_2.received, 5)
        self.assertEqual(line_2.remaining(), 8)

        # The 'on_order' quantity should have decreased by 10.5
        self.assertEqual(
            prt.on_order, round(on_order + Decimal(31.3) - Decimal(10.5), 1)
        )

        # The 'in_stock' quantity should have increased by 10.5
        self.assertEqual(prt.total_stock, round(in_stock + Decimal(10.5), 1))

        # Check that the unit purchase price value has been updated correctly
        si = StockItem.objects.filter(supplier_part=sp_1)
        self.assertEqual(si.count(), 1)

        # Ensure that received quantity and unit purchase price data are correct
        si = si.first()
        self.assertEqual(si.quantity, 10)
        self.assertEqual(si.purchase_price, Money(100, 'USD'))

        si = StockItem.objects.filter(supplier_part=sp_2)
        self.assertEqual(si.count(), 1)

        # Ensure that received quantity and unit purchase price data are correct
        si = si.first()
        self.assertEqual(si.quantity, 0.5)
        self.assertEqual(si.purchase_price, Money(100, 'USD'))

    def test_receive_convert_currency(self):
        """Test receiving orders with different currencies."""
        # Setup some dummy exchange rates
        self.generate_exchange_rates()

        set_global_setting('INVENTREE_DEFAULT_CURRENCY', 'USD')
        self.assertEqual(get_global_setting('INVENTREE_DEFAULT_CURRENCY'), 'USD')

        # Enable auto conversion
        set_global_setting('PURCHASEORDER_CONVERT_CURRENCY', True)

        order = PurchaseOrder.objects.get(pk=7)
        sku = SupplierPart.objects.get(SKU='ZERGM312')
        loc = StockLocation.objects.get(id=1)

        # Add a line item (in CAD)
        line = order.add_line_item(sku, 100, purchase_price=Money(1.25, 'CAD'))

        order.place_order()

        # Receive a line item, should be converted to GBP
        order.receive_line_item(line, loc, 50, user=None)
        item = order.stock_items.order_by('-pk').first()

        self.assertEqual(item.quantity, 50)
        self.assertEqual(item.purchase_price_currency, 'USD')
        self.assertAlmostEqual(item.purchase_price.amount, Decimal(0.7353), 3)

        # Disable auto conversion
        set_global_setting('PURCHASEORDER_CONVERT_CURRENCY', False)

        order.receive_line_item(line, loc, 30, user=None)
        item = order.stock_items.order_by('-pk').first()

        self.assertEqual(item.quantity, 30)
        self.assertEqual(item.purchase_price_currency, 'CAD')
        self.assertAlmostEqual(item.purchase_price.amount, Decimal(1.25), 3)

    def test_overdue_notification(self):
        """Test overdue purchase order notification.

        Ensure that a notification is sent when a PurchaseOrder becomes overdue
        """
        po = PurchaseOrder.objects.get(pk=1)

        # Created by 'sam'
        po.created_by = get_user_model().objects.get(pk=4)

        # Responsible : 'Engineers' group
        responsible = Owner.create(obj=Group.objects.get(pk=2))
        po.responsible = responsible

        # Target date = yesterday
        po.target_date = datetime.now().date() - timedelta(days=1)
        po.save()

        # Check for overdue purchase orders
        order.tasks.check_overdue_purchase_orders()

        for user_id in [2, 3, 4]:
            messages = common.models.NotificationMessage.objects.filter(
                category='order.overdue_purchase_order', user__id=user_id
            )

            # User ID 3 is inactive, and thus should not receive notifications
            if user_id == 3:
                self.assertFalse(messages.exists())
                continue
            else:
                self.assertTrue(messages.exists())

            msg = messages.first()

            self.assertEqual(msg.target_object_id, 1)
            self.assertEqual(msg.name, 'Overdue Purchase Order')

    def test_new_po_notification(self):
        """Test that a notification is sent when a new PurchaseOrder is created.

        - The responsible user(s) should receive a notification
        - The creating user should *not* receive a notification
        """
        po = PurchaseOrder.objects.create(
            supplier=Company.objects.get(pk=1),
            reference='XYZABC',
            created_by=get_user_model().objects.get(pk=3),
            responsible=Owner.create(obj=get_user_model().objects.get(pk=4)),
        )

        # Initially, no notifications

        messages = common.models.NotificationMessage.objects.filter(
            category='order.new_purchaseorder'
        )

        self.assertEqual(messages.count(), 0)

        # Place the order
        po.place_order()

        # A notification should have been generated for user 4 (who is a member of group 3)
        self.assertTrue(messages.filter(user__pk=4).exists())

        # However *no* notification should have been generated for the creating user
        self.assertFalse(messages.filter(user__pk=3).exists())

    def test_metadata(self):
        """Unit tests for the metadata field."""
        for model in [PurchaseOrder, PurchaseOrderLineItem, PurchaseOrderExtraLine]:
            p = model.objects.first()

            # Setting metadata to something *other* than a dict will fail
            with self.assertRaises(django_exceptions.ValidationError):
                p.metadata = 'test'
                p.save()

            # Reset metadata to known state
            p.metadata = {}

            self.assertIsNone(p.get_metadata('test'))
            self.assertEqual(p.get_metadata('test', backup_value=123), 123)

            # Test update via the set_metadata() method
            p.set_metadata('test', 3)
            self.assertEqual(p.get_metadata('test'), 3)

            for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
                p.set_metadata(k, k)

            self.assertEqual(len(p.metadata.keys()), 4)
