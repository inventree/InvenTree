from django.db.models import Sum
from django.core.exceptions import ValidationError

import datetime
from InvenTree.InvenTree.helpers import InvenTreeTestCate

from InvenTree.status_codes import StockHistoryCode

from .models import StockLocation, StockItem, StockItemTracking
from .models import StockItemTestResult

from part.models import Part
from build.models import Build


class StockTest(InvenTreeTestCate):
    """
    Tests to ensure that the stock location tree functions correcly
    """

    fixtures = [
        'category',
        'part',
        'test_templates',
        'location',
        'stock',
        'stock_tests',
    ]

    def setUp(self):
        super().setUp()

        # Extract some shortcuts from the fixtures
        self.home = StockLocation.objects.get(name='Home')
        self.bathroom = StockLocation.objects.get(name='Bathroom')
        self.diningroom = StockLocation.objects.get(name='Dining Room')

        self.office = StockLocation.objects.get(name='Office')
        self.drawer1 = StockLocation.objects.get(name='Drawer_1')
        self.drawer2 = StockLocation.objects.get(name='Drawer_2')
        self.drawer3 = StockLocation.objects.get(name='Drawer_3')

        # Ensure the MPTT objects are correctly rebuild
        Part.objects.rebuild()
        StockItem.objects.rebuild()

    def test_expiry(self):
        """
        Test expiry date functionality for StockItem model.
        """

        today = datetime.datetime.now().date()

        item = StockItem.objects.create(
            location=self.office,
            part=Part.objects.get(pk=1),
            quantity=10,
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
        """
        Test that the is_building flag does not count towards stock.
        """

        part = Part.objects.get(pk=1)

        # Record the total stock count
        n = part.total_stock

        StockItem.objects.create(part=part, quantity=5)

        # And there should be *no* items being build
        self.assertEqual(part.quantity_being_built, 0)

        build = Build.objects.create(reference='12345', part=part, title='A test build', quantity=1)

        # Add some stock items which are "building"
        for i in range(10):
            StockItem.objects.create(
                part=part, build=build,
                quantity=10, is_building=True
            )

        # The "is_building" quantity should not be counted here
        self.assertEqual(part.total_stock, n + 5)

        self.assertEqual(part.quantity_being_built, 1)

    def test_loc_count(self):
        self.assertEqual(StockLocation.objects.count(), 7)

    def test_url(self):
        it = StockItem.objects.get(pk=2)
        self.assertEqual(it.get_absolute_url(), '/stock/item/2/')

        self.assertEqual(self.home.get_absolute_url(), '/stock/location/1/')

    def test_barcode(self):
        barcode = self.office.format_barcode(brief=False)

        self.assertIn('"name": "Office"', barcode)

    def test_strings(self):
        it = StockItem.objects.get(pk=1)
        self.assertEqual(str(it), '4000 x M2x4 LPHS @ Dining Room')

    def test_parent_locations(self):

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
        self.assertTrue(self.office.has_children)

        self.assertFalse(self.drawer2.has_children)

        childs = [item.pk for item in self.office.getUniqueChildren()]

        self.assertIn(self.drawer1.id, childs)
        self.assertIn(self.drawer2.id, childs)

        self.assertNotIn(self.bathroom.id, childs)

    def test_items(self):
        self.assertTrue(self.drawer1.has_items())
        self.assertTrue(self.drawer3.has_items())
        self.assertFalse(self.drawer2.has_items())

        # Drawer 3 should have three stock items
        self.assertEqual(self.drawer3.stock_items.count(), 18)
        self.assertEqual(self.drawer3.item_count, 18)

    def test_stock_count(self):
        part = Part.objects.get(pk=1)
        entries = part.stock_entries()

        self.assertEqual(entries.count(), 2)

        # There should be 9000 screws in stock
        self.assertEqual(part.total_stock, 9000)

        # There should be 16 widgets "in stock"
        self.assertEqual(
            StockItem.objects.filter(part=25).aggregate(Sum('quantity'))['quantity__sum'], 16
        )

    def test_delete_location(self):

        # How many stock items are there?
        n_stock = StockItem.objects.count()

        # What parts are in drawer 3?
        stock_ids = [part.id for part in StockItem.objects.filter(location=self.drawer3.id)]

        # Delete location - parts should move to parent location
        self.drawer3.delete()

        # There should still be the same number of parts
        self.assertEqual(StockItem.objects.count(), n_stock)

        # stock should have moved
        for s_id in stock_ids:
            s_item = StockItem.objects.get(id=s_id)
            self.assertEqual(s_item.location, self.office)

    def test_move(self):
        """ Test stock movement functions """

        # Move 4,000 screws to the bathroom
        it = StockItem.objects.get(pk=1)
        self.assertNotEqual(it.location, self.bathroom)
        self.assertTrue(it.move(self.bathroom, 'Moved to the bathroom', None))
        self.assertEqual(it.location, self.bathroom)

        # There now should be 2 lots of screws in the bathroom
        self.assertEqual(StockItem.objects.filter(part=1, location=self.bathroom).count(), 2)

        # Check that a tracking item was added
        track = StockItemTracking.objects.filter(item=it).latest('id')

        self.assertEqual(track.item, it)
        self.assertEqual(track.tracking_type, StockHistoryCode.STOCK_MOVE)
        self.assertEqual(track.notes, 'Moved to the bathroom')

    def test_self_move(self):
        # Try to move an item to its current location (should fail)
        it = StockItem.objects.get(pk=1)

        n = it.tracking_info.count()
        self.assertFalse(it.move(it.location, 'Moved to same place', None))

        # Ensure tracking info was not added
        self.assertEqual(it.tracking_info.count(), n)

    def test_partial_move(self):
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
        it = StockItem.objects.get(pk=2)
        n = it.quantity
        it.add_stock(45, None, notes='Added some items')

        self.assertEqual(it.quantity, n + 45)

        # Check that a tracking item was added
        track = StockItemTracking.objects.filter(item=it).latest('id')

        self.assertEqual(track.tracking_type, StockHistoryCode.STOCK_ADD)
        self.assertIn('Added some items', track.notes)

        self.assertFalse(it.add_stock(-10, None))

    def test_take_stock(self):
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
        """
        Tests for stock serialization
        """

        p = Part.objects.create(
            name='trackable part',
            description='trackable part',
            trackable=True,
        )

        item = StockItem.objects.create(
            part=p,
            quantity=1,
        )

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
        """
        Unit tests for "large" serial numbers which exceed integer encoding
        """

        p = Part.objects.create(
            name='trackable part',
            description='trackable part',
            trackable=True,
        )

        item = StockItem.objects.create(
            part=p,
            quantity=1,
        )

        for sn in [12345, '12345', ' 12345 ']:
            item.serial = sn
            item.save()

            self.assertEqual(item.serial_int, 12345)

        item.serial = "-123"
        item.save()

        # Negative number should map to zero
        self.assertEqual(item.serial_int, 0)

        # Test a very very large value
        item.serial = '99999999999999999999999999999999999999999999999999999'
        item.save()

        self.assertEqual(item.serial_int, 0x7fffffff)

        # Non-numeric values should encode to zero
        for sn in ['apple', 'banana', 'carrot']:
            item.serial = sn
            item.save()

            self.assertEqual(item.serial_int, 0)

        # Next, test for incremenet / decrement functionality
        item.serial = 100
        item.save()

        item_next = StockItem.objects.create(
            part=p,
            serial=150,
            quantity=1
        )

        self.assertEqual(item.get_next_serialized_item(), item_next)

        item_prev = StockItem.objects.create(
            part=p,
            serial=' 57',
            quantity=1,
        )

        self.assertEqual(item.get_next_serialized_item(reverse=True), item_prev)

        # Create a number of serialized stock items around the current item
        for i in range(75, 125):
            try:
                StockItem.objects.create(
                    part=p,
                    serial=i,
                    quantity=1,
                )
            except:
                pass

        item_next = item.get_next_serialized_item()
        item_prev = item.get_next_serialized_item(reverse=True)

        self.assertEqual(item_next.serial_int, 101)
        self.assertEqual(item_prev.serial_int, 99)

    def test_serialize_stock_invalid(self):
        """
        Test manual serialization of parts.
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
            item.serializeStock("k", [], self.user)

        with self.assertRaises(ValidationError):
            item.serializeStock(-1, [], self.user)

        # Not enough serial numbers for all stock items.
        with self.assertRaises(ValidationError):
            item.serializeStock(3, "hello", self.user)

    def test_serialize_stock_valid(self):
        """ Perform valid stock serializations """

        # There are 10 of these in stock
        # Item will deplete when deleted
        item = StockItem.objects.get(pk=100)
        item.delete_on_deplete = True

        item.save()

        n = StockItem.objects.filter(part=25).count()

        self.assertEqual(item.quantity, 10)

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
        """
        Unit tests for stock location tree structure (MPTT).
        Ensure that the MPTT structure is rebuilt correctly,
        and the corrent ancestor tree is observed.

        Ref: https://github.com/inventree/InvenTree/issues/2636
        Ref: https://github.com/inventree/InvenTree/issues/2733
        """

        # First, we will create a stock location structure

        A = StockLocation.objects.create(
            name='A',
            description='Top level location'
        )

        B1 = StockLocation.objects.create(
            name='B1',
            parent=A
        )

        B2 = StockLocation.objects.create(
            name='B2',
            parent=A
        )

        B3 = StockLocation.objects.create(
            name='B3',
            parent=A
        )

        C11 = StockLocation.objects.create(
            name='C11',
            parent=B1,
        )

        C12 = StockLocation.objects.create(
            name='C12',
            parent=B1,
        )

        C21 = StockLocation.objects.create(
            name='C21',
            parent=B2,
        )

        C22 = StockLocation.objects.create(
            name='C22',
            parent=B2,
        )

        C31 = StockLocation.objects.create(
            name='C31',
            parent=B3,
        )

        C32 = StockLocation.objects.create(
            name='C32',
            parent=B3
        )

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
        for i in range(10):
            StockItem.objects.create(
                part=Part.objects.get(pk=1),
                quantity=10,
                location=B3
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


class VariantTest(StockTest):
    """
    Tests for calculation stock counts against templates / variants
    """

    def test_variant_stock(self):
        # Check the 'Chair' variant
        chair = Part.objects.get(pk=10000)

        # No stock items for the variant part itself
        self.assertEqual(chair.stock_entries(include_variants=False).count(), 0)

        self.assertEqual(chair.stock_entries().count(), 12)

        green = Part.objects.get(pk=10003)
        self.assertEqual(green.stock_entries(include_variants=False).count(), 0)
        self.assertEqual(green.stock_entries().count(), 3)

    def test_serial_numbers(self):
        # Test serial number functionality for variant / template parts

        chair = Part.objects.get(pk=10000)

        # Operations on the top-level object
        self.assertTrue(chair.checkIfSerialNumberExists(1))
        self.assertTrue(chair.checkIfSerialNumberExists(2))
        self.assertTrue(chair.checkIfSerialNumberExists(3))
        self.assertTrue(chair.checkIfSerialNumberExists(4))
        self.assertTrue(chair.checkIfSerialNumberExists(5))

        self.assertTrue(chair.checkIfSerialNumberExists(20))
        self.assertTrue(chair.checkIfSerialNumberExists(21))
        self.assertTrue(chair.checkIfSerialNumberExists(22))

        self.assertFalse(chair.checkIfSerialNumberExists(30))

        self.assertEqual(chair.getLatestSerialNumber(), '22')

        # Check for conflicting serial numbers
        to_check = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        conflicts = chair.find_conflicting_serial_numbers(to_check)

        self.assertEqual(len(conflicts), 6)

        # Same operations on a sub-item
        variant = Part.objects.get(pk=10003)
        self.assertEqual(variant.getLatestSerialNumber(), '22')

        # Create a new serial number
        n = variant.getLatestSerialNumber()

        item = StockItem(
            part=variant,
            quantity=1,
            serial=n
        )

        # This should fail
        with self.assertRaises(ValidationError):
            item.save()

        # Verify items with a non-numeric serial don't offer a next serial.
        item.serial = "string"
        item.save()

        self.assertEqual(variant.getLatestSerialNumber(), "string")

        # This should pass, although not strictly an int field now.
        item.serial = int(n) + 1
        item.save()

        # Attempt to create the same serial number but for a variant (should fail!)
        item.pk = None
        item.part = Part.objects.get(pk=10004)

        with self.assertRaises(ValidationError):
            item.save()

        item.serial += 1
        item.save()


class TestResultTest(StockTest):
    """
    Tests for the StockItemTestResult model.
    """

    def test_test_count(self):
        item = StockItem.objects.get(pk=105)
        tests = item.test_results
        self.assertEqual(tests.count(), 4)

        results = item.getTestResults(test="Temperature Test")
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

        item = StockItem.objects.get(pk=522)

        status = item.requiredTestStatus()

        self.assertEqual(status['total'], 5)
        self.assertEqual(status['passed'], 2)
        self.assertEqual(status['failed'], 2)

        self.assertFalse(item.passedAllRequiredTests())

        # Add some new test results to make it pass!
        test = StockItemTestResult.objects.get(pk=12345)
        test.result = True
        test.save()

        StockItemTestResult.objects.create(
            stock_item=item,
            test='sew cushion',
            result=True
        )

        # Still should be failing at this point,
        # as the most recent "apply paint" test was False
        self.assertFalse(item.passedAllRequiredTests())

        # Add a new test result against this required test
        StockItemTestResult.objects.create(
            stock_item=item,
            test='apply paint',
            date=datetime.datetime(2022, 12, 12),
            result=True
        )

        self.assertTrue(item.passedAllRequiredTests())

    def test_duplicate_item_tests(self):

        # Create an example stock item by copying one from the database (because we are lazy)
        item = StockItem.objects.get(pk=522)

        item.pk = None
        item.serial = None
        item.quantity = 50
        item.batch = "B344"

        item.save()

        # Do some tests!
        StockItemTestResult.objects.create(
            stock_item=item,
            test="Firmware",
            result=True
        )

        StockItemTestResult.objects.create(
            stock_item=item,
            test="Paint Color",
            result=True,
            value="Red"
        )

        StockItemTestResult.objects.create(
            stock_item=item,
            test="Applied Sticker",
            result=False
        )

        self.assertEqual(item.test_results.count(), 3)
        self.assertEqual(item.quantity, 50)

        # Split some items out
        item2 = item.splitStock(20, None, None)

        self.assertEqual(item.quantity, 30)

        self.assertEqual(item.test_results.count(), 3)
        self.assertEqual(item2.test_results.count(), 3)

        StockItemTestResult.objects.create(
            stock_item=item2,
            test='A new test'
        )

        self.assertEqual(item.test_results.count(), 3)
        self.assertEqual(item2.test_results.count(), 4)

        # Test StockItem serialization
        item2.serializeStock(1, [100], self.user)

        # Add a test result to the parent *after* serialization
        StockItemTestResult.objects.create(
            stock_item=item2,
            test='abcde'
        )

        self.assertEqual(item2.test_results.count(), 5)

        item3 = StockItem.objects.get(serial=100, part=item2.part)

        self.assertEqual(item3.test_results.count(), 4)

    def test_installed_tests(self):
        """
        Test test results for stock in stock.

        Or, test "test results" for "stock items" installed "inside" a "stock item"
        """

        # Get a "master" stock item
        item = StockItem.objects.get(pk=105)

        tests = item.testResultMap(include_installed=False)
        self.assertEqual(len(tests), 3)

        # There are no "sub items" intalled at this stage
        tests = item.testResultMap(include_installed=False)
        self.assertEqual(len(tests), 3)

        # Create a stock item which is installed *inside* the master item
        sub_item = StockItem.objects.create(
            part=item.part,
            quantity=1,
            belongs_to=item,
            location=None
        )

        # Now, create some test results against the sub item

        # First test is overshadowed by the same test for the parent part
        StockItemTestResult.objects.create(
            stock_item=sub_item,
            test='firmware version',
            date=datetime.datetime.now().date(),
            result=True
        )

        # Should return the same number of tests as before
        tests = item.testResultMap(include_installed=True)
        self.assertEqual(len(tests), 3)

        # Now, add a *unique* test result for the sub item
        StockItemTestResult.objects.create(
            stock_item=sub_item,
            test='some new test',
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
