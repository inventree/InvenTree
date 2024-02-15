"""Tests for stock app."""

import datetime

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.test import override_settings

from build.models import Build
from common.models import InvenTreeSetting
from company.models import Company
from InvenTree.status_codes import StockHistoryCode
from InvenTree.unit_test import InvenTreeTestCase
from order.models import SalesOrder
from part.models import Part, PartTestTemplate

from .models import StockItem, StockItemTestResult, StockItemTracking, StockLocation


class StockTestBase(InvenTreeTestCase):
    """Base class for running Stock tests."""

    fixtures = [
        'category',
        'part',
        'test_templates',
        'location',
        'stock',
        'stock_tests',
    ]

    @classmethod
    def setUpTestData(cls):
        """Setup for all tests."""
        super().setUpTestData()

        # Extract some shortcuts from the fixtures
        cls.home = StockLocation.objects.get(name='Home')
        cls.bathroom = StockLocation.objects.get(name='Bathroom')
        cls.diningroom = StockLocation.objects.get(name='Dining Room')

        cls.office = StockLocation.objects.get(name='Office')
        cls.drawer1 = StockLocation.objects.get(name='Drawer_1')
        cls.drawer2 = StockLocation.objects.get(name='Drawer_2')
        cls.drawer3 = StockLocation.objects.get(name='Drawer_3')

        # Ensure the MPTT objects are correctly rebuild
        Part.objects.rebuild()
        StockItem.objects.rebuild()


class StockTest(StockTestBase):
    """Tests to ensure that the stock location tree functions correctly."""

    def test_pathstring(self):
        """Check that pathstring updates occur as expected."""
        a = StockLocation.objects.create(name='A')
        b = StockLocation.objects.create(name='B', parent=a)
        c = StockLocation.objects.create(name='C', parent=b)
        d = StockLocation.objects.create(name='D', parent=c)

        def refresh():
            a.refresh_from_db()
            b.refresh_from_db()
            c.refresh_from_db()
            d.refresh_from_db()

        # Initial checks
        self.assertEqual(a.pathstring, 'A')
        self.assertEqual(b.pathstring, 'A/B')
        self.assertEqual(c.pathstring, 'A/B/C')
        self.assertEqual(d.pathstring, 'A/B/C/D')

        c.name = 'Cc'
        c.save()

        refresh()
        self.assertEqual(a.pathstring, 'A')
        self.assertEqual(b.pathstring, 'A/B')
        self.assertEqual(c.pathstring, 'A/B/Cc')
        self.assertEqual(d.pathstring, 'A/B/Cc/D')

        b.name = 'Bb'
        b.save()

        refresh()
        self.assertEqual(a.pathstring, 'A')
        self.assertEqual(b.pathstring, 'A/Bb')
        self.assertEqual(c.pathstring, 'A/Bb/Cc')
        self.assertEqual(d.pathstring, 'A/Bb/Cc/D')

        a.name = 'Aa'
        a.save()

        refresh()
        self.assertEqual(a.pathstring, 'Aa')
        self.assertEqual(b.pathstring, 'Aa/Bb')
        self.assertEqual(c.pathstring, 'Aa/Bb/Cc')
        self.assertEqual(d.pathstring, 'Aa/Bb/Cc/D')

        d.name = 'Dd'
        d.save()

        refresh()
        self.assertEqual(a.pathstring, 'Aa')
        self.assertEqual(b.pathstring, 'Aa/Bb')
        self.assertEqual(c.pathstring, 'Aa/Bb/Cc')
        self.assertEqual(d.pathstring, 'Aa/Bb/Cc/Dd')

        # Test a really long name
        # (it will be clipped to < 250 characters)
        a.name = 'A' * 100
        a.save()
        b.name = 'B' * 100
        b.save()
        c.name = 'C' * 100
        c.save()
        d.name = 'D' * 100
        d.save()

        refresh()
        self.assertEqual(len(a.pathstring), 100)
        self.assertEqual(len(b.pathstring), 201)
        self.assertEqual(len(c.pathstring), 249)
        self.assertEqual(len(d.pathstring), 249)

        self.assertTrue(d.pathstring.startswith('AAAAAAAA'))
        self.assertTrue(d.pathstring.endswith('DDDDDDDD'))

    def test_link(self):
        """Test the link URL field validation."""
        item = StockItem.objects.get(pk=1)

        # Check that invalid URLs fail
        for bad_url in ['test.com', 'httpx://abc.xyz', 'https:google.com']:
            with self.assertRaises(ValidationError):
                item.link = bad_url
                item.save()
                item.full_clean()

        # Check that valid URLs pass - and check custom schemes
        for good_url in [
            'https://test.com',
            'https://digikey.com/datasheets?file=1010101010101.bin',
            'ftp://download.com:8080/file.aspx',
        ]:
            item.link = good_url
            item.save()
            item.full_clean()

        # A long URL should fail
        long_url = 'https://website.co.uk?query=' + 'a' * 173

        with self.assertRaises(ValidationError):
            item.link = long_url
            item.full_clean()

        # Shorten by a single character, will pass
        long_url = long_url[:-1]

        item.link = long_url
        item.save()

    @override_settings(EXTRA_URL_SCHEMES=['ssh'])
    def test_exteneded_schema(self):
        """Test that extended URL schemes are allowed."""
        item = StockItem.objects.get(pk=1)
        item.link = 'ssh://user:pwd@deb.org:223'
        item.save()
        item.full_clean()

    def test_serial_numbers(self):
        """Test serial number uniqueness."""
        # Ensure that 'global uniqueness' setting is enabled
        InvenTreeSetting.set_setting('SERIAL_NUMBER_GLOBALLY_UNIQUE', True, self.user)

        part_a = Part.objects.create(
            name='A', description='A part with a description', trackable=True
        )
        part_b = Part.objects.create(
            name='B', description='B part with a description', trackable=True
        )

        # Create a StockItem for part_a
        StockItem.objects.create(part=part_a, quantity=1, serial='ABCDE')

        # Create a StockItem for part_a (but, will error due to identical serial)
        with self.assertRaises(ValidationError):
            StockItem.objects.create(part=part_b, quantity=1, serial='ABCDE')

        # Now, allow serial numbers to be duplicated between different parts
        InvenTreeSetting.set_setting('SERIAL_NUMBER_GLOBALLY_UNIQUE', False, self.user)

        StockItem.objects.create(part=part_b, quantity=1, serial='ABCDE')

    def test_expiry(self):
        """Test expiry date functionality for StockItem model."""
        today = datetime.datetime.now().date()

        item = StockItem.objects.create(
            location=self.office, part=Part.objects.get(pk=1), quantity=10
        )

        # Without an expiry_date set, item should not be "expired"
        self.assertFalse(item.is_expired())

        # Set the expiry date to today
        item.expiry_date = today
        item.save()

        self.assertFalse(item.is_expired())

        # Set the expiry date in the future
        item.expiry_date = today + datetime.timedelta(days=5)
        item.save()

        self.assertFalse(item.is_expired())

        # Set the expiry date in the past
        item.expiry_date = today - datetime.timedelta(days=5)
        item.save()

        self.assertTrue(item.is_expired())

    def test_is_building(self):
        """Test that the is_building flag does not count towards stock."""
        part = Part.objects.get(pk=1)

        # Record the total stock count
        n = part.total_stock

        StockItem.objects.create(part=part, quantity=5)

        # And there should be *no* items being build
        self.assertEqual(part.quantity_being_built, 0)

        build = Build.objects.create(
            reference='BO-4444', part=part, title='A test build', quantity=1
        )

        # Add some stock items which are "building"
        for _ in range(10):
            StockItem.objects.create(
                part=part, build=build, quantity=10, is_building=True
            )

        # The "is_building" quantity should not be counted here
        self.assertEqual(part.total_stock, n + 5)

        self.assertEqual(part.quantity_being_built, 1)

    def test_loc_count(self):
        """Test count function."""
        self.assertEqual(StockLocation.objects.count(), 7)

    def test_url(self):
        """Test get_absolute_url function."""
        it = StockItem.objects.get(pk=2)
        self.assertEqual(it.get_absolute_url(), '/stock/item/2/')

        self.assertEqual(self.home.get_absolute_url(), '/stock/location/1/')

    def test_strings(self):
        """Test str function."""
        it = StockItem.objects.get(pk=1)
        self.assertEqual(str(it), '4000 x M2x4 LPHS @ Dining Room')

    def test_parent_locations(self):
        """Test parent."""
        # Ensure pathstring gets updated
        self.drawer3.save()

        self.assertEqual(self.office.parent, None)
        self.assertEqual(self.drawer1.parent, self.office)
        self.assertEqual(self.drawer2.parent, self.office)
        self.assertEqual(self.drawer3.parent, self.office)

        self.assertEqual(self.drawer3.pathstring, 'Office/Drawer_3')

        # Move one of the drawers
        self.drawer3.parent = self.home
        self.drawer3.save()

        self.assertNotEqual(self.drawer3.parent, self.office)

        self.assertEqual(self.drawer3.pathstring, 'Home/Drawer_3')

    def test_children(self):
        """Test has_children."""
        self.assertTrue(self.office.has_children)

        self.assertFalse(self.drawer2.has_children)

        children = [item.pk for item in self.office.getUniqueChildren()]

        self.assertIn(self.drawer1.id, children)
        self.assertIn(self.drawer2.id, children)

        self.assertNotIn(self.bathroom.id, children)

    def test_items(self):
        """Test has_items."""
        # Drawer 3 should have three stock items
        self.assertEqual(self.drawer3.stock_items.count(), 18)
        self.assertEqual(self.drawer3.item_count, 18)

    def test_stock_count(self):
        """Test stock count."""
        part = Part.objects.get(pk=1)
        entries = part.stock_entries()

        self.assertEqual(entries.count(), 2)

        # There should be 9000 screws in stock
        self.assertEqual(part.total_stock, 9000)

        # There should be 16 widgets "in stock"
        self.assertEqual(
            StockItem.objects.filter(part=25).aggregate(Sum('quantity'))[
                'quantity__sum'
            ],
            16,
        )

    def test_delete_location(self):
        """Test deleting stock."""
        # How many stock items are there?
        n_stock = StockItem.objects.count()

        # What parts are in drawer 3?
        stock_ids = [
            part.id for part in StockItem.objects.filter(location=self.drawer3.id)
        ]

        # Delete location - parts should move to parent location
        self.drawer3.delete()

        # There should still be the same number of parts
        self.assertEqual(StockItem.objects.count(), n_stock)

        # stock should have moved
        for s_id in stock_ids:
            s_item = StockItem.objects.get(id=s_id)
            self.assertEqual(s_item.location, self.office)

    def test_move(self):
        """Test stock movement functions."""
        # Move 4,000 screws to the bathroom
        it = StockItem.objects.get(pk=1)
        self.assertNotEqual(it.location, self.bathroom)
        self.assertTrue(it.move(self.bathroom, 'Moved to the bathroom', None))
        self.assertEqual(it.location, self.bathroom)

        # There now should be 2 lots of screws in the bathroom
        self.assertEqual(
            StockItem.objects.filter(part=1, location=self.bathroom).count(), 2
        )

        # Check that a tracking item was added
        track = StockItemTracking.objects.filter(item=it).latest('id')

        self.assertEqual(track.item, it)
        self.assertEqual(track.tracking_type, StockHistoryCode.STOCK_MOVE)
        self.assertEqual(track.notes, 'Moved to the bathroom')

    def test_self_move(self):
        """Test moving stock to its current location."""
        it = StockItem.objects.get(pk=1)

        n = it.tracking_info.count()
        self.assertTrue(it.move(it.location, 'Moved to same place', None))

        # Ensure tracking info was not added
        self.assertEqual(it.tracking_info.count(), n + 1)

    def test_partial_move(self):
        """Test partial stock moving."""
        w1 = StockItem.objects.get(pk=100)

        # A batch code is required to split partial stock!
        w1.batch = 'BW1'
        w1.save()

        # Move 6 of the units
        self.assertTrue(w1.move(self.diningroom, 'Moved', None, quantity=6))

        # There should be 4 remaining
        self.assertEqual(w1.quantity, 4)

        # There should also be a new object still in drawer3
        self.assertEqual(StockItem.objects.filter(part=25).count(), 5)
        widget = StockItem.objects.get(location=self.drawer3.id, part=25, quantity=4)

        # Try to move negative units
        self.assertFalse(widget.move(self.bathroom, 'Test', None, quantity=-100))
        self.assertEqual(StockItem.objects.filter(part=25).count(), 5)

        # Try to move to a blank location
        self.assertFalse(widget.move(None, 'null', None))

    def test_split_stock(self):
        """Test stock splitting."""
        # Split the 1234 x 2K2 resistors in Drawer_1

        n = StockItem.objects.filter(part=3).count()

        stock = StockItem.objects.get(id=1234)
        stock.splitStock(1000, None, self.user)
        self.assertEqual(stock.quantity, 234)

        # There should be a new stock item too!
        self.assertEqual(StockItem.objects.filter(part=3).count(), n + 1)

        # Try to split a negative quantity
        stock.splitStock(-10, None, self.user)
        self.assertEqual(StockItem.objects.filter(part=3).count(), n + 1)

        stock.splitStock(stock.quantity, None, self.user)
        self.assertEqual(StockItem.objects.filter(part=3).count(), n + 1)

    def test_stocktake(self):
        """Test stocktake function."""
        # Perform stocktake
        it = StockItem.objects.get(pk=2)
        self.assertEqual(it.quantity, 5000)
        it.stocktake(255, None, notes='Counted items!')

        self.assertEqual(it.quantity, 255)

        # Check that a tracking item was added
        track = StockItemTracking.objects.filter(item=it).latest('id')

        self.assertEqual(track.tracking_type, StockHistoryCode.STOCK_COUNT)
        self.assertIn('Counted items', track.notes)

        n = it.tracking_info.count()
        self.assertFalse(it.stocktake(-1, None, 'test negative stocktake'))

        # Ensure tracking info was not added
        self.assertEqual(it.tracking_info.count(), n)

    def test_add_stock(self):
        """Test adding stock."""
        it = StockItem.objects.get(pk=2)
        n = it.quantity
        it.add_stock(45, None, notes='Added some items')

        self.assertEqual(it.quantity, n + 45)

        # Check that a tracking item was added
        track = StockItemTracking.objects.filter(item=it).latest('id')

        self.assertEqual(track.tracking_type, StockHistoryCode.STOCK_ADD)
        self.assertIn('Added some items', track.notes)

        self.assertFalse(it.add_stock(-10, None))

    def test_allocate_to_customer(self):
        """Test allocating stock to a customer."""
        it = StockItem.objects.get(pk=2)
        n = it.quantity
        an = n - 10
        customer = Company.objects.create(name='MyTestCompany')
        order = SalesOrder.objects.create(description='Test order')
        ait = it.allocateToCustomer(
            customer, quantity=an, order=order, user=None, notes='Allocated some stock'
        )

        # Check if new stockitem is created
        self.assertTrue(ait)
        # Check correct quantity of new allocated stock
        self.assertEqual(ait.quantity, an)
        # Check if new stock is assigned to correct customer
        self.assertEqual(ait.customer, customer)
        # Check if new stock is assigned to correct sales order
        self.assertEqual(ait.sales_order, order)
        # Check location is None because this stock is now allocated to a user
        self.assertFalse(ait.location)

        # Check that a tracking item was added
        track = StockItemTracking.objects.filter(item=ait).latest('id')

        self.assertEqual(
            track.tracking_type, StockHistoryCode.SHIPPED_AGAINST_SALES_ORDER
        )
        self.assertIn('Allocated some stock', track.notes)

    def test_return_from_customer(self):
        """Test removing previous allocated stock from customer."""
        it = StockItem.objects.get(pk=2)

        # First establish total stock for this part
        allstock_before = StockItem.objects.filter(part=it.part).aggregate(
            Sum('quantity')
        )['quantity__sum']

        n = it.quantity
        an = n - 10
        customer = Company.objects.create(name='MyTestCompany')
        order = SalesOrder.objects.create(description='Test order')

        ait = it.allocateToCustomer(
            customer, quantity=an, order=order, user=None, notes='Allocated some stock'
        )

        self.assertEqual(ait.quantity, an)
        self.assertTrue(ait.parent, it)

        # There should be only quantity 10x remaining
        it.refresh_from_db()
        self.assertEqual(it.quantity, 10)

        ait.return_from_customer(it.location, None, notes='Stock removed from customer')

        # When returned stock is returned to its original (parent) location, check that the parent has correct quantity
        it.refresh_from_db()
        self.assertEqual(it.quantity, n)

        ait = it.allocateToCustomer(
            customer, quantity=an, order=order, user=None, notes='Allocated some stock'
        )
        ait.return_from_customer(
            self.drawer3, None, notes='Stock removed from customer'
        )

        # Check correct assignment of the new location
        self.assertEqual(ait.location, self.drawer3)
        # We should be un allocated
        self.assertFalse(ait.is_allocated())
        # No customer should be assigned
        self.assertFalse(ait.customer)
        # We dont belong to anyone
        self.assertFalse(ait.belongs_to)
        # Assigned sales order should be None
        self.assertFalse(ait.sales_order)

        # Check that a tracking item was added
        track = StockItemTracking.objects.filter(item=ait).latest('id')

        self.assertEqual(track.tracking_type, StockHistoryCode.RETURNED_FROM_CUSTOMER)
        self.assertIn('Stock removed from customer', track.notes)

        # Establish total stock for the part after remove from customer to check that we still have the correct quantity in stock
        allstock_after = StockItem.objects.filter(part=it.part).aggregate(
            Sum('quantity')
        )['quantity__sum']
        self.assertEqual(allstock_before, allstock_after)

    def test_take_stock(self):
        """Test stock removal."""
        it = StockItem.objects.get(pk=2)
        n = it.quantity
        it.take_stock(15, None, notes='Removed some items')

        self.assertEqual(it.quantity, n - 15)

        # Check that a tracking item was added
        track = StockItemTracking.objects.filter(item=it).latest('id')

        self.assertEqual(track.tracking_type, StockHistoryCode.STOCK_REMOVE)
        self.assertIn('Removed some items', track.notes)
        self.assertTrue(it.has_tracking_info)

        # Test that negative quantity does nothing
        self.assertFalse(it.take_stock(-10, None))

    def test_deplete_stock(self):
        """Test depleted stock deletion."""
        w1 = StockItem.objects.get(pk=100)
        w2 = StockItem.objects.get(pk=101)

        # Take 25 units from w1 (there are only 10 in stock)
        w1.take_stock(30, None, notes='Took 30')

        # Get from database again
        w1 = StockItem.objects.get(pk=100)
        self.assertEqual(w1.quantity, 0)

        # Take 25 units from w2 (will be deleted)
        w2.take_stock(30, None, notes='Took 30')

        # This StockItem should now have been deleted
        with self.assertRaises(StockItem.DoesNotExist):
            w2 = StockItem.objects.get(pk=101)

    def test_serials(self):
        """Tests for stock serialization."""
        p = Part.objects.create(
            name='trackable part',
            description='A trackable part which can be tracked',
            trackable=True,
        )

        # Ensure we do not have unique serials enabled
        InvenTreeSetting.set_setting('SERIAL_NUMBER_GLOBALLY_UNIQUE', False, None)

        item = StockItem.objects.create(part=p, quantity=1)

        self.assertFalse(item.serialized)

        item.serial = None
        item.save()
        self.assertFalse(item.serialized)

        item.serial = '    '
        item.save()
        self.assertFalse(item.serialized)

        item.serial = ''
        item.save()
        self.assertFalse(item.serialized)

        item.serial = '1'
        item.save()
        self.assertTrue(item.serialized)

    def test_big_serials(self):
        """Unit tests for "large" serial numbers which exceed integer encoding."""
        p = Part.objects.create(
            name='trackable part',
            description='A trackable part with really big serial numbers',
            trackable=True,
        )

        item = StockItem.objects.create(part=p, quantity=1)

        for sn in [12345, '12345', ' 12345 ']:
            item.serial = sn
            item.save()

            self.assertEqual(item.serial_int, 12345)

        item.serial = '-123'
        item.save()

        # Negative number should map to positive value
        self.assertEqual(item.serial_int, 123)

        # Test a very very large value
        item.serial = '99999999999999999999999999999999999999999999999999999'
        item.save()

        # The 'integer' portion has been clipped to a maximum value
        self.assertEqual(item.serial_int, 0x7FFFFFFF)

        # Non-numeric values should encode to zero
        for sn in ['apple', 'banana', 'carrot']:
            item.serial = sn
            item.save()

            self.assertEqual(item.serial_int, 0)

        # Next, test for increment / decrement functionality
        item.serial = 100
        item.save()

        item_next = StockItem.objects.create(part=p, serial=150, quantity=1)

        self.assertEqual(item.get_next_serialized_item(), item_next)

        item_prev = StockItem.objects.create(part=p, serial=' 57', quantity=1)

        self.assertEqual(item.get_next_serialized_item(reverse=True), item_prev)

        # Create a number of serialized stock items around the current item
        for i in range(75, 125):
            try:
                StockItem.objects.create(part=p, serial=i, quantity=1)
            except Exception:
                pass

        item_next = item.get_next_serialized_item()
        item_prev = item.get_next_serialized_item(reverse=True)

        self.assertEqual(item_next.serial_int, 101)
        self.assertEqual(item_prev.serial_int, 99)

    def test_serialize_stock_invalid(self):
        """Test manual serialization of parts.

        Each of these tests should fail
        """
        # Test serialization of non-serializable part
        item = StockItem.objects.get(pk=1234)

        with self.assertRaises(ValidationError):
            item.serializeStock(5, [1, 2, 3, 4, 5], self.user)

        with self.assertRaises(ValidationError):
            item.serializeStock(5, [1, 2, 3], self.user)

        # Pick a StockItem which can actually be serialized
        item = StockItem.objects.get(pk=100)

        # Try an invalid quantity
        with self.assertRaises(ValidationError):
            item.serializeStock('k', [], self.user)

        with self.assertRaises(ValidationError):
            item.serializeStock(-1, [], self.user)

        # Not enough serial numbers for all stock items.
        with self.assertRaises(ValidationError):
            item.serializeStock(3, 'hello', self.user)

    def test_serialize_stock_valid(self):
        """Perform valid stock serializations."""
        # There are 10 of these in stock
        # Item will deplete when deleted
        item = StockItem.objects.get(pk=100)
        item.delete_on_deplete = True

        item.save()

        n = StockItem.objects.filter(part=25).count()

        self.assertEqual(item.quantity, 10)

        # Ensure we do not have unique serials enabled
        InvenTreeSetting.set_setting('SERIAL_NUMBER_GLOBALLY_UNIQUE', False, None)

        item.serializeStock(3, [1, 2, 3], self.user)

        self.assertEqual(item.quantity, 7)

        # Try to serialize again (with same serial numbers)
        with self.assertRaises(ValidationError):
            item.serializeStock(3, [1, 2, 3], self.user)

        # Try to serialize too many items
        with self.assertRaises(ValidationError):
            item.serializeStock(13, [1, 2, 3], self.user)

        # Serialize some more stock
        item.serializeStock(5, [6, 7, 8, 9, 10], self.user)

        self.assertEqual(item.quantity, 2)

        # There should be 8 more items now
        self.assertEqual(StockItem.objects.filter(part=25).count(), n + 8)

        # Serialize the remainder of the stock
        item.serializeStock(2, [99, 100], self.user)

    def test_location_tree(self):
        """Unit tests for stock location tree structure (MPTT).

        Ensure that the MPTT structure is rebuilt correctly,
        and the current ancestor tree is observed.

        Ref: https://github.com/inventree/InvenTree/issues/2636
        Ref: https://github.com/inventree/InvenTree/issues/2733
        """
        # First, we will create a stock location structure

        A = StockLocation.objects.create(name='A', description='Top level location')

        B1 = StockLocation.objects.create(name='B1', parent=A)

        B2 = StockLocation.objects.create(name='B2', parent=A)

        B3 = StockLocation.objects.create(name='B3', parent=A)

        C11 = StockLocation.objects.create(name='C11', parent=B1)

        C12 = StockLocation.objects.create(name='C12', parent=B1)

        C21 = StockLocation.objects.create(name='C21', parent=B2)

        C22 = StockLocation.objects.create(name='C22', parent=B2)

        C31 = StockLocation.objects.create(name='C31', parent=B3)

        C32 = StockLocation.objects.create(name='C32', parent=B3)

        # Check that the tree_id is correct for each sublocation
        for loc in [B1, B2, B3, C11, C12, C21, C22, C31, C32]:
            self.assertEqual(loc.tree_id, A.tree_id)

        # Check that the tree levels are correct for each node in the tree

        self.assertEqual(A.level, 0)
        self.assertEqual(A.get_ancestors().count(), 0)

        for loc in [B1, B2, B3]:
            self.assertEqual(loc.parent, A)
            self.assertEqual(loc.level, 1)
            self.assertEqual(loc.get_ancestors().count(), 1)

        for loc in [C11, C12]:
            self.assertEqual(loc.parent, B1)
            self.assertEqual(loc.level, 2)
            self.assertEqual(loc.get_ancestors().count(), 2)

        for loc in [C21, C22]:
            self.assertEqual(loc.parent, B2)
            self.assertEqual(loc.level, 2)
            self.assertEqual(loc.get_ancestors().count(), 2)

        for loc in [C31, C32]:
            self.assertEqual(loc.parent, B3)
            self.assertEqual(loc.level, 2)
            self.assertEqual(loc.get_ancestors().count(), 2)

        # Spot-check for C32
        ancestors = C32.get_ancestors(include_self=True)

        self.assertEqual(ancestors[0], A)
        self.assertEqual(ancestors[1], B3)
        self.assertEqual(ancestors[2], C32)

        # At this point, we are confident that the tree is correctly structured.

        # Let's delete node B3 from the tree. We expect that:
        # - C31 should move directly under A
        # - C32 should move directly under A

        # Add some stock items to B3
        for _ in range(10):
            StockItem.objects.create(
                part=Part.objects.get(pk=1), quantity=10, location=B3
            )

        self.assertEqual(StockItem.objects.filter(location=B3).count(), 10)
        self.assertEqual(StockItem.objects.filter(location=A).count(), 0)

        B3.delete()

        A.refresh_from_db()
        C31.refresh_from_db()
        C32.refresh_from_db()

        # Stock items have been moved to A
        self.assertEqual(StockItem.objects.filter(location=A).count(), 10)

        # Parent should be A
        self.assertEqual(C31.parent, A)
        self.assertEqual(C32.parent, A)

        self.assertEqual(C31.tree_id, A.tree_id)
        self.assertEqual(C31.level, 1)

        self.assertEqual(C32.tree_id, A.tree_id)
        self.assertEqual(C32.level, 1)

        # Ancestor tree should be just A
        ancestors = C31.get_ancestors()
        self.assertEqual(ancestors.count(), 1)
        self.assertEqual(ancestors[0], A)

        ancestors = C32.get_ancestors()
        self.assertEqual(ancestors.count(), 1)
        self.assertEqual(ancestors[0], A)

        # Delete A
        A.delete()

        # Stock items have been moved to top-level location
        self.assertEqual(StockItem.objects.filter(location=None).count(), 10)

        for loc in [B1, B2, C11, C12, C21, C22]:
            loc.refresh_from_db()

        self.assertEqual(B1.parent, None)
        self.assertEqual(B2.parent, None)

        self.assertEqual(C11.parent, B1)
        self.assertEqual(C12.parent, B1)
        self.assertEqual(C11.get_ancestors().count(), 1)
        self.assertEqual(C12.get_ancestors().count(), 1)

        self.assertEqual(C21.parent, B2)
        self.assertEqual(C22.parent, B2)

        ancestors = C21.get_ancestors()

        self.assertEqual(C21.get_ancestors().count(), 1)
        self.assertEqual(C22.get_ancestors().count(), 1)

    def test_metadata(self):
        """Unit tests for the metadata field."""
        for model in [StockItem, StockLocation]:
            p = model.objects.first()

            self.assertIsNone(p.get_metadata('test'))
            self.assertEqual(p.get_metadata('test', backup_value=123), 123)

            # Test update via the set_metadata() method
            p.set_metadata('test', 3)
            self.assertEqual(p.get_metadata('test'), 3)

            for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
                p.set_metadata(k, k)

            self.assertEqual(len(p.metadata.keys()), 4)


class StockBarcodeTest(StockTestBase):
    """Run barcode tests for the stock app."""

    def test_stock_item_barcode_basics(self):
        """Simple tests for the StockItem barcode integration."""
        item = StockItem.objects.get(pk=1)

        self.assertEqual(StockItem.barcode_model_type(), 'stockitem')

        # Call format_barcode method
        barcode = item.format_barcode(brief=False)

        for key in ['tool', 'version', 'instance', 'stockitem']:
            self.assertIn(key, barcode)

        # Render simple barcode data for the StockItem
        barcode = item.barcode
        self.assertEqual(barcode, '{"stockitem": 1}')

    def test_location_barcode_basics(self):
        """Simple tests for the StockLocation barcode integration."""
        self.assertEqual(StockLocation.barcode_model_type(), 'stocklocation')

        loc = StockLocation.objects.get(pk=1)

        barcode = loc.format_barcode(brief=True)
        self.assertEqual('{"stocklocation": 1}', barcode)


class VariantTest(StockTestBase):
    """Tests for calculation stock counts against templates / variants."""

    def test_variant_stock(self):
        """Test variant functions."""
        # Check the 'Chair' variant
        chair = Part.objects.get(pk=10000)

        # No stock items for the variant part itself
        self.assertEqual(chair.stock_entries(include_variants=False).count(), 0)

        self.assertEqual(chair.stock_entries().count(), 12)

        green = Part.objects.get(pk=10003)
        self.assertEqual(green.stock_entries(include_variants=False).count(), 0)
        self.assertEqual(green.stock_entries().count(), 3)

    def test_serial_numbers(self):
        """Test serial number functionality for variant / template parts."""
        InvenTreeSetting.set_setting('SERIAL_NUMBER_GLOBALLY_UNIQUE', False, self.user)

        chair = Part.objects.get(pk=10000)

        # Operations on the top-level object
        [
            self.assertFalse(chair.validate_serial_number(i))
            for i in [1, 2, 3, 4, 5, 20, 21, 22]
        ]

        self.assertFalse(chair.validate_serial_number(20))
        self.assertFalse(chair.validate_serial_number(21))
        self.assertFalse(chair.validate_serial_number(22))

        self.assertTrue(chair.validate_serial_number(30))

        self.assertEqual(chair.get_latest_serial_number(), '22')

        # Check for conflicting serial numbers
        to_check = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        conflicts = chair.find_conflicting_serial_numbers(to_check)

        self.assertEqual(len(conflicts), 6)

        # Same operations on a sub-item
        variant = Part.objects.get(pk=10003)
        self.assertEqual(variant.get_latest_serial_number(), '22')

        # Create a new serial number
        n = variant.get_latest_serial_number()

        item = StockItem(part=variant, quantity=1, serial=n)

        # This should fail
        with self.assertRaises(ValidationError):
            item.save()

        # This should pass, although not strictly an int field now.
        item.serial = int(n) + 1
        item.save()

        # Attempt to create the same serial number but for a variant (should fail!)
        item.pk = None
        item.part = Part.objects.get(pk=10004)

        with self.assertRaises(ValidationError):
            item.save()

        item.serial = int(n) + 2
        item.save()


class StockTreeTest(StockTestBase):
    """Unit test for StockItem tree structure."""

    def test_stock_split(self):
        """Test that stock splitting works correctly."""
        StockItem.objects.rebuild()

        part = Part.objects.create(name='My part', description='My part description')
        location = StockLocation.objects.create(name='Test Location')

        # Create an initial stock item
        item = StockItem.objects.create(part=part, quantity=1000, location=location)

        # Test that the initial MPTT values are correct
        self.assertEqual(item.level, 0)
        self.assertEqual(item.lft, 1)
        self.assertEqual(item.rght, 2)

        children = []

        self.assertEqual(item.get_descendants(include_self=False).count(), 0)
        self.assertEqual(item.get_descendants(include_self=True).count(), 1)

        # Create child items by splitting stock
        for idx in range(10):
            child = item.splitStock(50, None, None)
            children.append(child)

            # Check that the child item has been correctly created
            self.assertEqual(child.parent.pk, item.pk)
            self.assertEqual(child.tree_id, item.tree_id)
            self.assertEqual(child.level, 1)

            item.refresh_from_db()
            self.assertEqual(item.get_children().count(), idx + 1)
            self.assertEqual(item.get_descendants(include_self=True).count(), idx + 2)

        item.refresh_from_db()
        n = item.get_descendants(include_self=True).count()

        for child in children:
            # Create multiple sub-childs
            for _idx in range(3):
                sub_child = child.splitStock(10, None, None)
                self.assertEqual(sub_child.parent.pk, child.pk)
                self.assertEqual(sub_child.tree_id, child.tree_id)
                self.assertEqual(sub_child.level, 2)

                self.assertEqual(sub_child.get_ancestors(include_self=True).count(), 3)

            child.refresh_from_db()
            self.assertEqual(child.get_descendants(include_self=True).count(), 4)

        item.refresh_from_db()
        self.assertEqual(item.get_descendants(include_self=True).count(), n + 30)


class TestResultTest(StockTestBase):
    """Tests for the StockItemTestResult model."""

    def test_test_count(self):
        """Test test count."""
        item = StockItem.objects.get(pk=105)
        tests = item.test_results
        self.assertEqual(tests.count(), 4)

        results = item.getTestResults(test='Temperature Test')
        self.assertEqual(results.count(), 2)

        # Passing tests
        self.assertEqual(item.getTestResults(result=True).count(), 3)
        self.assertEqual(item.getTestResults(result=False).count(), 1)

        # Result map
        result_map = item.testResultMap()

        self.assertEqual(len(result_map), 3)

        # Keys are all lower-case and do not contain spaces
        for test in ['firmwareversion', 'settingschecksum', 'temperaturetest']:
            self.assertIn(test, result_map.keys())

    def test_test_results(self):
        """Test test results."""
        item = StockItem.objects.get(pk=522)

        status = item.requiredTestStatus()

        self.assertEqual(status['total'], 5)
        self.assertEqual(status['passed'], 2)
        self.assertEqual(status['failed'], 1)

        self.assertFalse(item.passedAllRequiredTests())

        # Add some new test results to make it pass!
        test = StockItemTestResult.objects.get(pk=8)
        test.result = False
        test.save()

        status = item.requiredTestStatus()
        self.assertEqual(status['total'], 5)
        self.assertEqual(status['passed'], 1)
        self.assertEqual(status['failed'], 2)

        template = PartTestTemplate.objects.get(pk=3)

        StockItemTestResult.objects.create(
            stock_item=item, template=template, result=True
        )

        # Still should be failing at this point,
        # as the most recent "apply paint" test was False
        self.assertFalse(item.passedAllRequiredTests())

        template = PartTestTemplate.objects.get(pk=2)

        # Add a new test result against this required test
        StockItemTestResult.objects.create(
            stock_item=item,
            template=template,
            date=datetime.datetime(2022, 12, 12),
            result=True,
        )

        self.assertFalse(item.passedAllRequiredTests())

        # Generate a passing result for all required tests
        for template in item.part.getRequiredTests():
            StockItemTestResult.objects.create(
                stock_item=item,
                template=template,
                result=True,
                date=datetime.datetime(2025, 12, 12),
            )

        self.assertTrue(item.passedAllRequiredTests())

    def test_duplicate_item_tests(self):
        """Test duplicate item behaviour."""
        # Create an example stock item by copying one from the database (because we are lazy)

        from plugin.registry import registry

        StockItem.objects.rebuild()

        item = StockItem.objects.get(pk=522)

        item.pk = None
        item.serial = None
        item.quantity = 50

        # Try with an invalid batch code (according to sample validation plugin)
        item.batch = 'X234'

        # Ensure that the sample validation plugin is activated
        registry.set_plugin_state('validator', True)

        with self.assertRaises(ValidationError):
            item.save()

        item.batch = 'B123'
        item.save()

        # Do some tests!
        StockItemTestResult.objects.create(
            stock_item=item, test='Firmware', result=True
        )

        StockItemTestResult.objects.create(
            stock_item=item, test='Paint Color', result=True, value='Red'
        )

        StockItemTestResult.objects.create(
            stock_item=item, test='Applied Sticker', result=False
        )

        self.assertEqual(item.test_results.count(), 3)
        self.assertEqual(item.quantity, 50)

        # Split some items out
        item2 = item.splitStock(20, None, None)

        self.assertEqual(item.quantity, 30)

        self.assertEqual(item.test_results.count(), 3)
        self.assertEqual(item2.test_results.count(), 3)

        StockItemTestResult.objects.create(stock_item=item2, test='A new test')

        self.assertEqual(item.test_results.count(), 3)
        self.assertEqual(item2.test_results.count(), 4)

        # Test StockItem serialization
        item2.serializeStock(1, [100], self.user)

        # Add a test result to the parent *after* serialization
        StockItemTestResult.objects.create(stock_item=item2, test='abcde')

        self.assertEqual(item2.test_results.count(), 5)

        item3 = StockItem.objects.get(serial=100, part=item2.part)

        self.assertEqual(item3.test_results.count(), 4)

    def test_installed_tests(self):
        """Test test results for stock in stock.

        Or, test "test results" for "stock items" installed "inside" a "stock item"
        """
        # Get a "master" stock item
        item = StockItem.objects.get(pk=105)

        tests = item.testResultMap(include_installed=False)
        self.assertEqual(len(tests), 3)

        # There are no "sub items" installed at this stage
        tests = item.testResultMap(include_installed=False)
        self.assertEqual(len(tests), 3)

        # Create a stock item which is installed *inside* the master item
        sub_item = StockItem.objects.create(
            part=item.part, quantity=1, belongs_to=item, location=None
        )

        # Now, create some test results against the sub item
        # Ensure there is a matching PartTestTemplate
        if template := PartTestTemplate.objects.filter(
            part=item.part, key='firmwareversion'
        ).first():
            pass
        else:
            template = PartTestTemplate.objects.create(
                part=item.part, test_name='Firmware Version', required=True
            )

        # First test is overshadowed by the same test for the parent part
        StockItemTestResult.objects.create(
            stock_item=sub_item,
            template=template,
            date=datetime.datetime.now().date(),
            result=True,
        )

        # Should return the same number of tests as before
        tests = item.testResultMap(include_installed=True)
        self.assertEqual(len(tests), 3)

        if template := PartTestTemplate.objects.filter(
            part=item.part, key='somenewtest'
        ).first():
            pass
        else:
            template = PartTestTemplate.objects.create(
                part=item.part, test_name='Some New Test', required=True
            )

        # Now, add a *unique* test result for the sub item
        StockItemTestResult.objects.create(
            stock_item=sub_item,
            template=template,
            date=datetime.datetime.now().date(),
            result=False,
            value='abcde',
        )

        tests = item.testResultMap(include_installed=True)
        self.assertEqual(len(tests), 4)

        self.assertIn('somenewtest', tests)
        self.assertEqual(sub_item.test_results.count(), 2)

        # Check that asking for test result map for *top item only* still works
        tests = item.testResultMap(include_installed=False)
        self.assertEqual(len(tests), 3)
        self.assertNotIn('somenewtest', tests)
