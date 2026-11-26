"""Tests for the STOCK_ALLOW_EXPIRED_BUILD and STOCK_ALLOW_EXPIRED_SALE settings.

When stock expiry is enabled, expired stock may only be allocated to build orders
(or sales orders) if the corresponding setting permits it.
"""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.urls import reverse

import InvenTree.helpers
from build.models import Build, BuildItem, BuildLine
from build.status_codes import BuildStatus
from common.settings import set_global_setting
from company.models import Company
from InvenTree.unit_test import InvenTreeAPITestCase
from order.models import (
    SalesOrder,
    SalesOrderAllocation,
    SalesOrderLineItem,
    SalesOrderShipment,
)
from part.models import BomItem, Part
from stock.models import StockItem, StockLocation


class ExpiredAllocationTestBase(InvenTreeAPITestCase):
    """Common data for expired allocation tests."""

    roles = ['build.add', 'build.change', 'sales_order.add', 'sales_order.change']

    @classmethod
    def setUpTestData(cls):
        """Create parts, stock, a build order and a sales order."""
        super().setUpTestData()

        cls.location = StockLocation.objects.create(name='Expiry Store')

        cls.component = Part.objects.create(
            name='Expiring Component', component=True, salable=True
        )

        cls.assembly = Part.objects.create(name='Expiry Assembly', assembly=True)

        BomItem.objects.create(part=cls.assembly, sub_part=cls.component, quantity=1)

        today = InvenTree.helpers.current_date()

        cls.expired = StockItem.objects.create(
            part=cls.component,
            quantity=10,
            location=cls.location,
            expiry_date=today - timedelta(days=10),
        )

        cls.customer = Company.objects.create(name='Expiry Customer', is_customer=True)

    def setUp(self):
        """Enable stock expiry by default."""
        super().setUp()
        self.set_rules(expiry=True, build=False, sale=False)

    def set_rules(self, expiry: bool, build: bool, sale: bool):
        """Configure the stock expiry settings."""
        set_global_setting('STOCK_ENABLE_EXPIRY', expiry)
        set_global_setting('STOCK_ALLOW_EXPIRED_BUILD', build)
        set_global_setting('STOCK_ALLOW_EXPIRED_SALE', sale)

    def fresh_stock(self, quantity=10):
        """Create a stock item which has not expired."""
        return StockItem.objects.create(
            part=self.component,
            quantity=quantity,
            location=self.location,
            expiry_date=InvenTree.helpers.current_date() + timedelta(days=30),
        )


class BuildExpiredAllocationTest(ExpiredAllocationTestBase):
    """Allocation of expired stock to build orders."""

    def setUp(self):
        """Create a build order for each test."""
        super().setUp()

        self.build = Build.objects.create(
            part=self.assembly,
            quantity=5,
            reference='BO-9876',
            status=BuildStatus.PRODUCTION,
        )

        self.line = BuildLine.objects.get(build=self.build)

    def allocate(self, item, expected_code):
        """Allocate a stock item against the build via the API."""
        return self.post(
            reverse('api-build-allocate', kwargs={'pk': self.build.pk}),
            {
                'items': [
                    {'build_line': self.line.pk, 'stock_item': item.pk, 'quantity': 1}
                ]
            },
            expected_code=expected_code,
        )

    def test_api_blocked(self):
        """Expired stock cannot be allocated when not permitted."""
        response = self.allocate(self.expired, 400)
        self.assertIn('Expired stock cannot be used', str(response.data))
        self.assertFalse(BuildItem.objects.filter(stock_item=self.expired).exists())

        # Stock which has not expired can still be allocated
        self.allocate(self.fresh_stock(), 201)

    def test_api_allowed(self):
        """Expired stock can be allocated when permitted (or when expiry is disabled)."""
        self.set_rules(expiry=True, build=True, sale=False)
        self.allocate(self.expired, 201)

        BuildItem.objects.all().delete()

        self.set_rules(expiry=False, build=False, sale=False)
        self.allocate(self.expired, 201)

    def test_auto_allocate(self):
        """Auto-allocation skips expired stock when not permitted."""
        self.build.auto_allocate_stock()
        self.assertEqual(self.build.allocated_stock.count(), 0)

        # With fresh stock available, only the fresh stock is allocated
        fresh = self.fresh_stock()
        self.build.auto_allocate_stock()
        self.assertEqual(
            list(self.build.allocated_stock.values_list('stock_item', flat=True)),
            [fresh.pk],
        )

    def test_auto_allocate_allowed(self):
        """Auto-allocation uses expired stock when permitted."""
        self.set_rules(expiry=True, build=True, sale=False)

        self.build.auto_allocate_stock()
        self.assertEqual(
            list(self.build.allocated_stock.values_list('stock_item', flat=True)),
            [self.expired.pk],
        )

    def test_model_validation(self):
        """A new BuildItem cannot allocate expired stock, but existing allocations remain editable."""
        with self.assertRaises(ValidationError):
            BuildItem(build_line=self.line, stock_item=self.expired, quantity=1).clean()

        # Allocate while permitted, then disallow
        self.set_rules(expiry=True, build=True, sale=False)
        item = BuildItem.objects.create(
            build_line=self.line, stock_item=self.expired, quantity=1
        )
        self.set_rules(expiry=True, build=False, sale=False)

        item.quantity = 2
        item.clean()
        item.save()


class SalesOrderExpiredAllocationTest(ExpiredAllocationTestBase):
    """Allocation of expired stock to sales orders."""

    def setUp(self):
        """Create a sales order for each test."""
        super().setUp()

        self.order = SalesOrder.objects.create(
            customer=self.customer, reference='SO-9876'
        )
        self.shipment = SalesOrderShipment.objects.create(
            order=self.order, reference='1'
        )
        self.line = SalesOrderLineItem.objects.create(
            order=self.order, part=self.component, quantity=5
        )

    def allocate(self, item, expected_code):
        """Allocate a stock item against the sales order via the API."""
        return self.post(
            reverse('api-so-allocate', kwargs={'pk': self.order.pk}),
            {
                'items': [
                    {'line_item': self.line.pk, 'stock_item': item.pk, 'quantity': 1}
                ],
                'shipment': self.shipment.pk,
            },
            expected_code=expected_code,
        )

    def test_api_blocked(self):
        """Expired stock cannot be allocated when not permitted."""
        response = self.allocate(self.expired, 400)
        self.assertIn('Expired stock cannot be used', str(response.data))

        self.allocate(self.fresh_stock(), 201)

    def test_api_allowed(self):
        """Expired stock can be allocated when permitted (or when expiry is disabled)."""
        self.set_rules(expiry=True, build=False, sale=True)
        self.allocate(self.expired, 201)

        SalesOrderAllocation.objects.all().delete()

        self.set_rules(expiry=False, build=False, sale=False)
        self.allocate(self.expired, 201)

    def test_auto_allocate(self):
        """Auto-allocation skips expired stock when not permitted."""
        self.order.auto_allocate_stock(shipment=self.shipment)
        self.assertFalse(SalesOrderAllocation.objects.filter(line=self.line).exists())

        self.set_rules(expiry=True, build=False, sale=True)
        self.order.auto_allocate_stock(shipment=self.shipment)
        self.assertTrue(
            SalesOrderAllocation.objects.filter(
                line=self.line, item=self.expired
            ).exists()
        )

    def test_serial_allocation(self):
        """Expired serialized stock cannot be allocated by serial number when not permitted."""
        tracked = Part.objects.create(
            name='Expiring Tracked', salable=True, trackable=True
        )
        StockItem.objects.create(
            part=tracked,
            quantity=1,
            serial='EXP-1',
            location=self.location,
            expiry_date=InvenTree.helpers.current_date() - timedelta(days=1),
        )
        line = SalesOrderLineItem.objects.create(
            order=self.order, part=tracked, quantity=1
        )

        with self.assertRaises(ValidationError):
            self.order.allocate_serial_numbers(line, 1, 'EXP-1', self.shipment)

        self.set_rules(expiry=True, build=False, sale=True)
        allocations = self.order.allocate_serial_numbers(
            line, 1, 'EXP-1', self.shipment
        )
        self.assertEqual(len(allocations), 1)

    def test_model_validation(self):
        """A new allocation cannot use expired stock, but existing allocations remain editable."""
        with self.assertRaises(ValidationError):
            SalesOrderAllocation(
                line=self.line, shipment=self.shipment, item=self.expired, quantity=1
            ).clean()

        self.set_rules(expiry=True, build=False, sale=True)
        allocation = SalesOrderAllocation.objects.create(
            line=self.line, shipment=self.shipment, item=self.expired, quantity=1
        )
        self.set_rules(expiry=True, build=False, sale=False)

        allocation.quantity = 2
        allocation.clean()
        allocation.save()
