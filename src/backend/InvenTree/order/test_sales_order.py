"""Unit tests for the SalesOrder models."""

from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase

import order.tasks
from common.models import InvenTreeSetting, NotificationMessage
from company.models import Company
from InvenTree import status_codes as status
from InvenTree.unit_test import addUserPermission
from order.models import (
    SalesOrder,
    SalesOrderAllocation,
    SalesOrderExtraLine,
    SalesOrderLineItem,
    SalesOrderShipment,
)
from part.models import Part
from stock.models import StockItem
from users.models import Owner


class SalesOrderTest(TestCase):
    """Run tests to ensure that the SalesOrder model is working correctly."""

    fixtures = ['users']

    @classmethod
    def setUpTestData(cls):
        """Initial setup for this set of unit tests."""
        # Create a Company to ship the goods to
        cls.customer = Company.objects.create(
            name='ABC Co', description='My customer', is_customer=True
        )

        # Create a Part to ship
        cls.part = Part.objects.create(
            name='Spanner',
            salable=True,
            description='A spanner that I sell',
            is_template=True,
        )
        cls.variant = Part.objects.create(
            name='Blue Spanner',
            salable=True,
            description='A blue spanner that I sell',
            variant_of=cls.part,
        )

        # Create some stock!
        cls.Sa = StockItem.objects.create(part=cls.part, quantity=100)
        cls.Sb = StockItem.objects.create(part=cls.part, quantity=200)
        cls.Sc = StockItem.objects.create(part=cls.variant, quantity=100)

        # Create a SalesOrder to ship against
        cls.order = SalesOrder.objects.create(
            customer=cls.customer, reference='SO-1234', customer_reference='ABC 55555'
        )

        # Create a Shipment against this SalesOrder
        cls.shipment = SalesOrderShipment.objects.create(
            order=cls.order, reference='SO-001'
        )

        # Create a line item
        cls.line = SalesOrderLineItem.objects.create(
            quantity=50, order=cls.order, part=cls.part
        )

        # Create an extra line
        cls.extraline = SalesOrderExtraLine.objects.create(
            quantity=1, order=cls.order, reference='Extra line'
        )

    def test_so_reference(self):
        """Unit tests for sales order generation."""
        # Test that a good reference is created when we have no existing orders
        SalesOrder.objects.all().delete()

        self.assertEqual(SalesOrder.generate_reference(), 'SO-0001')

    def test_rebuild_reference(self):
        """Test that the 'reference_int' field gets rebuilt when the model is saved."""
        self.assertEqual(self.order.reference_int, 1234)

        self.order.reference = '999'
        self.order.save()
        self.assertEqual(self.order.reference_int, 999)

        self.order.reference = '1000K'
        self.order.save()
        self.assertEqual(self.order.reference_int, 1000)

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
        """Test for an empty order."""
        self.assertEqual(self.line.quantity, 50)
        self.assertEqual(self.line.allocated_quantity(), 0)
        self.assertEqual(self.line.fulfilled_quantity(), 0)
        self.assertFalse(self.line.is_fully_allocated())
        self.assertFalse(self.line.is_overallocated())

        self.assertTrue(self.order.is_pending)
        self.assertFalse(self.order.is_fully_allocated())

    def test_add_duplicate_line_item(self):
        """Adding a duplicate line item to a SalesOrder is accepted."""
        for ii in range(1, 5):
            SalesOrderLineItem.objects.create(
                order=self.order, part=self.part, quantity=ii
            )

    def allocate_stock(self, full=True):
        """Allocate stock to the order."""
        SalesOrderAllocation.objects.create(
            line=self.line,
            shipment=self.shipment,
            item=StockItem.objects.get(pk=self.Sa.pk),
            quantity=25,
        )

        SalesOrderAllocation.objects.create(
            line=self.line,
            shipment=self.shipment,
            item=StockItem.objects.get(pk=self.Sb.pk),
            quantity=25 if full else 20,
        )

    def test_over_allocate(self):
        """Test that over allocation logic works."""
        SA = StockItem.objects.create(part=self.part, quantity=9)

        # First three allocations should succeed
        for _i in range(3):
            allocation = SalesOrderAllocation.objects.create(
                line=self.line, item=SA, quantity=3, shipment=self.shipment
            )

        # Editing an existing allocation with a larger quantity should fail
        with self.assertRaises(ValidationError):
            allocation.quantity = 4
            allocation.save()
            allocation.clean()

        # Next allocation should fail
        with self.assertRaises(ValidationError):
            allocation = SalesOrderAllocation.objects.create(
                line=self.line, item=SA, quantity=3, shipment=self.shipment
            )

            allocation.clean()

    def test_allocate_partial(self):
        """Partially allocate stock."""
        self.allocate_stock(False)

        self.assertFalse(self.order.is_fully_allocated())
        self.assertFalse(self.line.is_fully_allocated())
        self.assertEqual(self.line.allocated_quantity(), 45)
        self.assertEqual(self.line.fulfilled_quantity(), 0)

    def test_allocate_full(self):
        """Fully allocate stock."""
        self.allocate_stock(True)

        self.assertTrue(self.order.is_fully_allocated())
        self.assertTrue(self.line.is_fully_allocated())
        self.assertEqual(self.line.allocated_quantity(), 50)

    def test_allocate_variant(self):
        """Allocate a variant of the designated item."""
        SalesOrderAllocation.objects.create(
            line=self.line,
            shipment=self.shipment,
            item=StockItem.objects.get(pk=self.Sc.pk),
            quantity=50,
        )
        self.assertEqual(self.line.allocated_quantity(), 50)

    def test_order_cancel(self):
        """Allocate line items then cancel the order."""
        self.allocate_stock(True)

        self.assertEqual(SalesOrderAllocation.objects.count(), 2)
        self.assertEqual(self.order.status, status.SalesOrderStatus.PENDING)

        self.order.cancel_order()
        self.assertEqual(SalesOrderAllocation.objects.count(), 0)
        self.assertEqual(self.order.status, status.SalesOrderStatus.CANCELLED)

        with self.assertRaises(ValidationError):
            self.order.can_complete(raise_error=True)

        # Now try to ship it - should fail
        result = self.order.ship_order(None)
        self.assertFalse(result)

    def test_complete_order(self):
        """Allocate line items, then ship the order."""
        # Assert some stuff before we run the test
        # Initially there are three stock items
        self.assertEqual(StockItem.objects.count(), 3)

        # Take 25 units from each StockItem
        self.allocate_stock(True)

        self.assertEqual(SalesOrderAllocation.objects.count(), 2)

        # Attempt to ship the order (but shipments are not completed!)
        result = self.order.ship_order(None)

        self.assertFalse(result)

        self.assertIsNone(self.shipment.shipment_date)
        self.assertFalse(self.shipment.is_complete())

        # Mark the shipments as complete
        self.shipment.complete_shipment(None)
        self.assertTrue(self.shipment.is_complete())

        # Now, should be OK to ship
        result = self.order.ship_order(None)

        self.assertTrue(result)

        self.assertEqual(self.order.status, status.SalesOrderStatus.SHIPPED)
        self.assertIsNotNone(self.order.shipment_date)

        # There should now be 5 stock items
        self.assertEqual(StockItem.objects.count(), 5)

        sa = StockItem.objects.get(pk=self.Sa.pk)
        sb = StockItem.objects.get(pk=self.Sb.pk)
        sc = StockItem.objects.get(pk=self.Sc.pk)

        # 25 units subtracted from each of the original non-variant items
        self.assertEqual(sa.quantity, 75)
        self.assertEqual(sb.quantity, 175)
        self.assertEqual(sc.quantity, 100)

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
        """Test sales order default shipment creation."""
        # Default setting value should be False
        self.assertEqual(
            False, InvenTreeSetting.get_setting('SALESORDER_DEFAULT_SHIPMENT')
        )

        # Create an order
        order_1 = SalesOrder.objects.create(
            customer=self.customer, reference='1235', customer_reference='ABC 55556'
        )

        # Order should have no shipments when setting is False
        self.assertEqual(0, order_1.shipment_count)

        # Update setting to True
        InvenTreeSetting.set_setting('SALESORDER_DEFAULT_SHIPMENT', True, None)
        self.assertEqual(
            True, InvenTreeSetting.get_setting('SALESORDER_DEFAULT_SHIPMENT')
        )

        # Create a second order
        order_2 = SalesOrder.objects.create(
            customer=self.customer, reference='1236', customer_reference='ABC 55557'
        )

        # Order should have one shipment
        self.assertEqual(1, order_2.shipment_count)
        self.assertEqual(1, order_2.pending_shipments().count())

        # Shipment should have default reference of '1'
        self.assertEqual('1', order_2.pending_shipments()[0].reference)

    def test_shipment_delivery(self):
        """Test the shipment delivery settings."""
        # Shipment delivery date should be empty before setting date
        self.assertIsNone(self.shipment.delivery_date)
        self.assertFalse(self.shipment.is_delivered())

    def test_overdue_notification(self):
        """Test overdue sales order notification."""
        user = get_user_model().objects.get(pk=3)

        addUserPermission(user, 'order', 'salesorder', 'view')
        user.is_active = True
        user.save()

        self.order.created_by = user
        self.order.responsible = Owner.create(obj=Group.objects.get(pk=2))
        self.order.target_date = datetime.now().date() - timedelta(days=1)
        self.order.save()

        # Check for overdue sales orders
        order.tasks.check_overdue_sales_orders()

        messages = NotificationMessage.objects.filter(
            category='order.overdue_sales_order'
        )

        self.assertEqual(len(messages), 1)

    def test_new_so_notification(self):
        """Test that a notification is sent when a new SalesOrder is issued.

        - The responsible user should receive a notification
        - The creating user should *not* receive a notification
        """
        so = SalesOrder.objects.create(
            customer=self.customer,
            reference='1234567',
            created_by=get_user_model().objects.get(pk=3),
            responsible=Owner.create(obj=Group.objects.get(pk=3)),
        )

        so.issue_order()

        messages = NotificationMessage.objects.filter(category='order.new_salesorder')

        # A notification should have been generated for user 4 (who is a member of group 3)
        self.assertTrue(messages.filter(user__pk=4).exists())

        # However *no* notification should have been generated for the creating user
        self.assertFalse(messages.filter(user__pk=3).exists())

    def test_metadata(self):
        """Unit tests for the metadata field."""
        for model in [
            SalesOrder,
            SalesOrderLineItem,
            SalesOrderExtraLine,
            SalesOrderShipment,
        ]:
            p = model.objects.first()

            self.assertIsNone(p.get_metadata('test'))
            self.assertEqual(p.get_metadata('test', backup_value=123), 123)

            # Test update via the set_metadata() method
            p.set_metadata('test', 3)
            self.assertEqual(p.get_metadata('test'), 3)

            for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
                p.set_metadata(k, k)

            self.assertEqual(len(p.metadata.keys()), 4)
