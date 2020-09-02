# -*- coding: utf-8 -*-

from django.test import TestCase

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError

from build.models import Build, BuildItem
from stock.models import StockItem
from part.models import Part, BomItem
from InvenTree import status_codes as status

from InvenTree.helpers import ExtractSerialNumbers


class BuildTest(TestCase):
    """
    Run some tests to ensure that the Build model is working properly.
    """

    def setUp(self):
        """
        Initialize data to use for these tests.
        """

        # Create a base "Part"
        self.assembly = Part.objects.create(
            name="An assembled part",
            description="Why does it matter what my description is?",
            assembly=True,
            trackable=True,
        )

        self.sub_part_1 = Part.objects.create(
            name="Widget A",
            description="A widget",
            component=True
        )

        self.sub_part_2 = Part.objects.create(
            name="Widget B",
            description="A widget",
            component=True
        )

        # Create BOM item links for the parts
        BomItem.objects.create(
            part=self.assembly,
            sub_part=self.sub_part_1,
            quantity=10
        )

        BomItem.objects.create(
            part=self.assembly,
            sub_part=self.sub_part_2,
            quantity=25
        )

        # Create a "Build" object to make 10x objects
        self.build = Build.objects.create(
            title="This is a build",
            part=self.assembly,
            quantity=10
        )

        # Create some stock items to assign to the build
        self.stock_1_1 = StockItem.objects.create(part=self.sub_part_1, quantity=1000)
        self.stock_1_2 = StockItem.objects.create(part=self.sub_part_1, quantity=100)

        self.stock_2_1 = StockItem.objects.create(part=self.sub_part_2, quantity=5000)

    def test_init(self):
        # Perform some basic tests before we start the ball rolling

        self.assertEqual(StockItem.objects.count(), 3)
        self.assertEqual(self.build.status, status.BuildStatus.PENDING)
        self.assertFalse(self.build.isFullyAllocated())

        self.assertFalse(self.build.isPartFullyAllocated(self.sub_part_1))
        self.assertFalse(self.build.isPartFullyAllocated(self.sub_part_2))

        self.assertEqual(self.build.getRequiredQuantity(self.sub_part_1), 100)
        self.assertEqual(self.build.getRequiredQuantity(self.sub_part_2), 250)

        self.assertTrue(self.build.can_build)
        self.assertFalse(self.build.is_complete)

        # Delete some stock and see if the build can still be completed
        self.stock_2_1.delete()
        self.assertFalse(self.build.can_build)

    def test_build_item_clean(self):
        # Ensure that dodgy BuildItem objects cannot be created

        stock = StockItem.objects.create(part=self.assembly, quantity=99)

        # Create a BuiltItem which points to an invalid StockItem
        b = BuildItem(stock_item=stock, build=self.build, quantity=10)
        
        with self.assertRaises(ValidationError):
            b.clean()

        # Create a BuildItem which has too much stock assigned
        b = BuildItem(stock_item=self.stock_1_1, build=self.build, quantity=9999999)

        with self.assertRaises(ValidationError):
            b.clean()

        # Negative stock? Not on my watch!
        b = BuildItem(stock_item=self.stock_1_1, build=self.build, quantity=-99)

        with self.assertRaises(ValidationError):
            b.clean()

    def test_duplicate_bom_line(self):
        # Try to add a duplicate BOM item - it should fail!

        with self.assertRaises(IntegrityError):
            BomItem.objects.create(
                part=self.assembly,
                sub_part=self.sub_part_1,
                quantity=99
            )

    def allocate_stock(self, q11, q12, q21):
        # Assign stock to this build

        BuildItem.objects.create(
            build=self.build,
            stock_item=self.stock_1_1,
            quantity=q11
        )

        BuildItem.objects.create(
            build=self.build,
            stock_item=self.stock_1_2,
            quantity=q12
        )

        BuildItem.objects.create(
            build=self.build,
            stock_item=self.stock_2_1,
            quantity=q21
        )

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                BuildItem.objects.create(
                    build=self.build,
                    stock_item=self.stock_2_1,
                    quantity=99
                )

        self.assertEqual(BuildItem.objects.count(), 3)

    def test_partial_allocation(self):

        self.allocate_stock(50, 50, 200)

        self.assertFalse(self.build.isFullyAllocated())
        self.assertTrue(self.build.isPartFullyAllocated(self.sub_part_1))
        self.assertFalse(self.build.isPartFullyAllocated(self.sub_part_2))

        self.build.unallocateStock()
        self.assertEqual(BuildItem.objects.count(), 0)

    def test_auto_allocate(self):

        allocations = self.build.getAutoAllocations()

        self.assertEqual(len(allocations), 1)

        self.build.autoAllocate()
        self.assertEqual(BuildItem.objects.count(), 1)
        self.assertTrue(self.build.isPartFullyAllocated(self.sub_part_2))

    def test_cancel(self):

        self.allocate_stock(50, 50, 200)
        self.build.cancelBuild(None)

        self.assertEqual(BuildItem.objects.count(), 0)

    def test_complete(self):

        self.allocate_stock(50, 50, 250)

        self.assertTrue(self.build.isFullyAllocated())

        # Generate some serial numbers!
        serials = ExtractSerialNumbers("1-10", 10)

        self.build.completeBuild(None, serials, None)

        self.assertEqual(self.build.status, status.BuildStatus.COMPLETE)

        # the original BuildItem objects should have been deleted!
        self.assertEqual(BuildItem.objects.count(), 0)

        # New stock items should have been created!
        # - Ten for the build output (as the part was serialized)
        # - Three for the split items assigned to the build
        self.assertEqual(StockItem.objects.count(), 16)

        A = StockItem.objects.get(pk=self.stock_1_1.pk)
        B = StockItem.objects.get(pk=self.stock_1_2.pk)
        C = StockItem.objects.get(pk=self.stock_2_1.pk)

        # Stock should have been subtracted from the original items
        self.assertEqual(A.quantity, 950)
        self.assertEqual(B.quantity, 50)
        self.assertEqual(C.quantity, 4750)

        # New stock items should have also been allocated to the build
        allocated = StockItem.objects.filter(build_order=self.build)

        self.assertEqual(allocated.count(), 3)

        q = sum([item.quantity for item in allocated.all()])

        self.assertEqual(q, 350)
        
        # And 10 new stock items created for the build output
        outputs = StockItem.objects.filter(build=self.build)

        self.assertEqual(outputs.count(), 10)
