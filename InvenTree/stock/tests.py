from django.test import TestCase

from .models import StockLocation, StockItem, StockItemTracking
from part.models import Part


class StockTest(TestCase):
    """
    Tests to ensure that the stock location tree functions correcly
    """

    def setUp(self):
        # Initialize some categories
        self.loc1 = StockLocation.objects.create(name='L0',
                                                 description='Top level category',
                                                 parent=None)

        self.loc2 = StockLocation.objects.create(name='L1.1',
                                                 description='Second level 1/2',
                                                 parent=self.loc1)

        self.loc3 = StockLocation.objects.create(name='L1.2',
                                                 description='Second level 2/2',
                                                 parent=self.loc1)

        self.loc4 = StockLocation.objects.create(name='L2.1',
                                                 description='Third level 1/2',
                                                 parent=self.loc2)

        self.loc5 = StockLocation.objects.create(name='L2.2',
                                                 description='Third level 2/2',
                                                 parent=self.loc3)

        # Add some items to loc4 (all copies of a single part)
        p = Part.objects.create(name='ACME Part', description='This is a part!')

        StockItem.objects.create(part=p, location=self.loc4, quantity=1000)
        StockItem.objects.create(part=p, location=self.loc4, quantity=250)
        StockItem.objects.create(part=p, location=self.loc4, quantity=12)

    def test_simple(self):
        it = StockItem.objects.get(pk=2)
        self.assertEqual(it.get_absolute_url(), '/stock/item/2/')
        self.assertEqual(self.loc4.get_absolute_url(), '/stock/location/4/')

    def test_strings(self):
        it = StockItem.objects.get(pk=2)
        self.assertEqual(str(it), '250 x ACME Part @ L2.1')

    def test_parent(self):
        self.assertEqual(StockLocation.objects.count(), 5)
        self.assertEqual(self.loc1.parent, None)
        self.assertEqual(self.loc2.parent, self.loc1)
        self.assertEqual(self.loc5.parent, self.loc3)

    def test_children(self):
        self.assertTrue(self.loc1.has_children)
        self.assertFalse(self.loc5.has_children)

        childs = self.loc1.getUniqueChildren()

        self.assertIn(self.loc2.id, childs)
        self.assertIn(self.loc4.id, childs)

    def test_paths(self):
        self.assertEqual(self.loc5.pathstring, 'L0/L1.2/L2.2')

    def test_items(self):
        # Location 5 should have no items
        self.assertFalse(self.loc5.has_items())
        self.assertFalse(self.loc3.has_items())

        # Location 4 should have three stock items
        self.assertEqual(self.loc4.stock_items.count(), 3)

    def test_stock_count(self):
        part = Part.objects.get(pk=1)

        # There should be 1262 items in stock
        self.assertEqual(part.total_stock, 1262)

    def test_delete_location(self):
        # Delete location - parts should move to parent location
        self.loc4.delete()

        # There should still be 3 stock items
        self.assertEqual(StockItem.objects.count(), 3)

        # Parent location should have moved up to loc2
        for it in StockItem.objects.all():
            self.assertEqual(it.location, self.loc2)

    def test_move(self):
        # Move the first stock item to loc5
        it = StockItem.objects.get(pk=1)
        self.assertNotEqual(it.location, self.loc5)
        self.assertTrue(it.move(self.loc5, 'Moved to another place', None))
        self.assertEqual(it.location, self.loc5)

        # Check that a tracking item was added
        track = StockItemTracking.objects.filter(item=it).latest('id')

        self.assertEqual(track.item, it)
        self.assertIn('Moved to', track.title)
        self.assertEqual(track.notes, 'Moved to another place')

    def test_self_move(self):
        # Try to move an item to its current location (should fail)
        it = StockItem.objects.get(pk=1)

        n = it.tracking_info.count()
        self.assertFalse(it.move(it.location, 'Moved to same place', None))

        # Ensure tracking info was not added
        self.assertEqual(it.tracking_info.count(), n)

    def test_stocktake(self):
        # Perform stocktake
        it = StockItem.objects.get(pk=2)
        self.assertEqual(it.quantity, 250)
        it.stocktake(255, None, notes='Counted items!')

        self.assertEqual(it.quantity, 255)

        # Check that a tracking item was added
        track = StockItemTracking.objects.filter(item=it).latest('id')

        self.assertIn('Stocktake', track.title)
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

        self.assertIn('Added', track.title)
        self.assertIn('Added some items', track.notes)

    def test_take_stock(self):
        it = StockItem.objects.get(pk=2)
        n = it.quantity
        it.take_stock(15, None, notes='Removed some items')

        self.assertEqual(it.quantity, n - 15)

        # Check that a tracking item was added
        track = StockItemTracking.objects.filter(item=it).latest('id')

        self.assertIn('Removed', track.title)
        self.assertIn('Removed some items', track.notes)
        self.assertTrue(it.has_tracking_info)
