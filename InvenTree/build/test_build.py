# -*- coding: utf-8 -*-

from django.test import TestCase

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from build.models import Build, BuildItem
from stock.models import StockItem
from part.models import Part, BomItem
from InvenTree import status_codes as status


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

        # Create some build output (StockItem) objects
        self.output_1 = StockItem.objects.create(
            part=self.assembly,
            quantity=5,
            is_building=True,
            build=self.build
        )

        self.output_2 = StockItem.objects.create(
            part=self.assembly,
            quantity=5,
            is_building=True,
            build=self.build,
        )

        # Create some stock items to assign to the build
        self.stock_1_1 = StockItem.objects.create(part=self.sub_part_1, quantity=1000)
        self.stock_1_2 = StockItem.objects.create(part=self.sub_part_1, quantity=100)

        self.stock_2_1 = StockItem.objects.create(part=self.sub_part_2, quantity=5000)

    def test_init(self):
        # Perform some basic tests before we start the ball rolling

        self.assertEqual(StockItem.objects.count(), 5)
        
        # Build is PENDING
        self.assertEqual(self.build.status, status.BuildStatus.PENDING)

        # Build has two build outputs
        self.assertEqual(self.build.output_count, 2)

        # None of the build outputs have been completed
        for output in self.build.get_build_outputs().all():
            self.assertFalse(self.build.isFullyAllocated(output))

        self.assertFalse(self.build.isPartFullyAllocated(self.sub_part_1, self.output_1))
        self.assertFalse(self.build.isPartFullyAllocated(self.sub_part_2, self.output_2))

        self.assertEqual(self.build.unallocatedQuantity(self.sub_part_1, self.output_1), 50)
        self.assertEqual(self.build.unallocatedQuantity(self.sub_part_1, self.output_2), 50)
        self.assertEqual(self.build.unallocatedQuantity(self.sub_part_2, self.output_1), 125)
        self.assertEqual(self.build.unallocatedQuantity(self.sub_part_2, self.output_2), 125)

        self.assertFalse(self.build.is_complete)

    def test_build_item_clean(self):
        # Ensure that dodgy BuildItem objects cannot be created

        stock = StockItem.objects.create(part=self.assembly, quantity=99)

        # Create a BuiltItem which points to an invalid StockItem
        b = BuildItem(stock_item=stock, build=self.build, quantity=10)
        
        with self.assertRaises(ValidationError):
            b.save()

        # Create a BuildItem which has too much stock assigned
        b = BuildItem(stock_item=self.stock_1_1, build=self.build, quantity=9999999)

        with self.assertRaises(ValidationError):
            b.clean()

        # Negative stock? Not on my watch!
        b = BuildItem(stock_item=self.stock_1_1, build=self.build, quantity=-99)

        with self.assertRaises(ValidationError):
            b.clean()

        # Ok, what about we make one that does *not* fail?
        b = BuildItem(stock_item=self.stock_1_1, build=self.build, install_into=self.output_1, quantity=10)
        b.save()

    def test_duplicate_bom_line(self):
        # Try to add a duplicate BOM item - it should fail!

        with self.assertRaises(IntegrityError):
            BomItem.objects.create(
                part=self.assembly,
                sub_part=self.sub_part_1,
                quantity=99
            )

    def allocate_stock(self, q11, q12, q21, output):
        # Assign stock to this build

        if q11 > 0:
            BuildItem.objects.create(
                build=self.build,
                stock_item=self.stock_1_1,
                quantity=q11,
                install_into=output
            )

        if q12 > 0:
            BuildItem.objects.create(
                build=self.build,
                stock_item=self.stock_1_2,
                quantity=q12,
                install_into=output
            )

        if q21 > 0:
            BuildItem.objects.create(
                build=self.build,
                stock_item=self.stock_2_1,
                quantity=q21,
                install_into=output,
            )

            # Attempt to create another identical BuildItem
            b = BuildItem(
                build=self.build,
                stock_item=self.stock_2_1,
                quantity=q21
            )

            with self.assertRaises(ValidationError):
                b.clean()

    def test_partial_allocation(self):
        """
        Partially allocate against output 1
        """

        self.allocate_stock(50, 50, 200, self.output_1)

        self.assertTrue(self.build.isFullyAllocated(self.output_1))
        self.assertFalse(self.build.isFullyAllocated(self.output_2))
        self.assertTrue(self.build.isPartFullyAllocated(self.sub_part_1, self.output_1))
        self.assertTrue(self.build.isPartFullyAllocated(self.sub_part_2, self.output_1))
        
        self.assertFalse(self.build.isPartFullyAllocated(self.sub_part_1, self.output_2))
        self.assertFalse(self.build.isPartFullyAllocated(self.sub_part_2, self.output_2))

        # Check that the part has been allocated
        self.assertEqual(self.build.allocatedQuantity(self.sub_part_1, self.output_1), 100)

        self.build.unallocateStock(output=self.output_1)
        self.assertEqual(BuildItem.objects.count(), 0)

        # Check that the part has been unallocated
        self.assertEqual(self.build.allocatedQuantity(self.sub_part_1, self.output_1), 0)

    def test_auto_allocate(self):
        """
        Test auto-allocation functionality against the build outputs
        """

        allocations = self.build.getAutoAllocations(self.output_1)

        self.assertEqual(len(allocations), 1)

        self.build.autoAllocate(self.output_1)
        self.assertEqual(BuildItem.objects.count(), 1)

        # Check that one part has been fully allocated to the build output
        self.assertTrue(self.build.isPartFullyAllocated(self.sub_part_2, self.output_1))

        # But, the *other* build output has not been allocated against
        self.assertFalse(self.build.isPartFullyAllocated(self.sub_part_2, self.output_2))

    def test_cancel(self):
        """
        Test cancellation of the build
        """

        # TODO

        """
        self.allocate_stock(50, 50, 200, self.output_1)
        self.build.cancelBuild(None)

        self.assertEqual(BuildItem.objects.count(), 0)
        """
        pass

    def test_complete(self):
        """
        Test completion of a build output
        """

        self.allocate_stock(50, 50, 250, self.output_1)
        self.allocate_stock(50, 50, 250, self.output_2)

        self.assertTrue(self.build.isFullyAllocated(self.output_1))
        self.assertTrue(self.build.isFullyAllocated(self.output_2))

        self.build.completeBuildOutput(self.output_1, None)

        self.assertFalse(self.build.can_complete)

        self.build.completeBuildOutput(self.output_2, None)

        self.assertTrue(self.build.can_complete)

        self.build.complete_build(None)
    
        self.assertEqual(self.build.status, status.BuildStatus.COMPLETE)

        # the original BuildItem objects should have been deleted!
        self.assertEqual(BuildItem.objects.count(), 0)

        # New stock items should have been created!
        self.assertEqual(StockItem.objects.count(), 4)

        a = StockItem.objects.get(pk=self.stock_1_1.pk)

        # This stock item has been depleted!
        with self.assertRaises(StockItem.DoesNotExist):
            StockItem.objects.get(pk=self.stock_1_2.pk)
        
        c = StockItem.objects.get(pk=self.stock_2_1.pk)

        # Stock should have been subtracted from the original items
        self.assertEqual(a.quantity, 900)
        self.assertEqual(c.quantity, 4500)
        
        # And 10 new stock items created for the build output
        outputs = StockItem.objects.filter(build=self.build)

        self.assertEqual(outputs.count(), 2)

        for output in outputs:
            self.assertFalse(output.is_building)
