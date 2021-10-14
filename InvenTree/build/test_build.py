# -*- coding: utf-8 -*-

from django.test import TestCase

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from InvenTree import status_codes as status

from build.models import Build, BuildItem, get_next_build_number
from part.models import Part, BomItem
from stock.models import StockItem
from stock.tasks import delete_old_stock_items


class BuildTest(TestCase):
    """
    Run some tests to ensure that the Build model is working properly.
    """

    def setUp(self):
        """
        Initialize data to use for these tests.

        The base Part 'assembly' has a BOM consisting of three parts:

        - 5 x sub_part_1
        - 3 x sub_part_2
        - 2 x sub_part_3 (trackable)

        We will build 10x 'assembly' parts, in two build outputs:

        - 3 x output_1
        - 7 x output_2

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

        self.sub_part_3 = Part.objects.create(
            name="Widget C",
            description="A widget",
            component=True,
            trackable=True
        )

        # Create BOM item links for the parts
        BomItem.objects.create(
            part=self.assembly,
            sub_part=self.sub_part_1,
            quantity=5
        )

        BomItem.objects.create(
            part=self.assembly,
            sub_part=self.sub_part_2,
            quantity=3
        )

        # sub_part_3 is trackable!
        BomItem.objects.create(
            part=self.assembly,
            sub_part=self.sub_part_3,
            quantity=2
        )

        ref = get_next_build_number()

        if ref is None:
            ref = "0001"

        # Create a "Build" object to make 10x objects
        self.build = Build.objects.create(
            reference=ref,
            title="This is a build",
            part=self.assembly,
            quantity=10
        )

        # Create some build output (StockItem) objects
        self.output_1 = StockItem.objects.create(
            part=self.assembly,
            quantity=3,
            is_building=True,
            build=self.build
        )

        self.output_2 = StockItem.objects.create(
            part=self.assembly,
            quantity=7,
            is_building=True,
            build=self.build,
        )

        # Create some stock items to assign to the build
        self.stock_1_1 = StockItem.objects.create(part=self.sub_part_1, quantity=1000)
        self.stock_1_2 = StockItem.objects.create(part=self.sub_part_1, quantity=100)

        self.stock_2_1 = StockItem.objects.create(part=self.sub_part_2, quantity=5000)

        self.stock_3_1 = StockItem.objects.create(part=self.sub_part_3, quantity=1000)

    def test_init(self):
        # Perform some basic tests before we start the ball rolling

        self.assertEqual(StockItem.objects.count(), 6)

        # Build is PENDING
        self.assertEqual(self.build.status, status.BuildStatus.PENDING)

        # Build has two build outputs
        self.assertEqual(self.build.output_count, 2)

        # None of the build outputs have been completed
        for output in self.build.get_build_outputs().all():
            self.assertFalse(self.build.isFullyAllocated(output))

        self.assertFalse(self.build.isPartFullyAllocated(self.sub_part_1, self.output_1))
        self.assertFalse(self.build.isPartFullyAllocated(self.sub_part_2, self.output_2))

        self.assertEqual(self.build.unallocatedQuantity(self.sub_part_1, self.output_1), 15)
        self.assertEqual(self.build.unallocatedQuantity(self.sub_part_1, self.output_2), 35)
        self.assertEqual(self.build.unallocatedQuantity(self.sub_part_2, self.output_1), 9)
        self.assertEqual(self.build.unallocatedQuantity(self.sub_part_2, self.output_2), 21)

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

    def allocate_stock(self, output, allocations):
        """
        Allocate stock to this build, against a particular output

        Args:
            output - StockItem object (or None)
            allocations - Map of {StockItem: quantity}
        """

        for item, quantity in allocations.items():
            BuildItem.objects.create(
                build=self.build,
                stock_item=item,
                quantity=quantity,
                install_into=output
            )

    def test_partial_allocation(self):
        """
        Test partial allocation of stock
        """

        # Fully allocate tracked stock against build output 1
        self.allocate_stock(
            self.output_1,
            {
                self.stock_3_1: 6,
            }
        )

        self.assertTrue(self.build.isFullyAllocated(self.output_1))

        # Partially allocate tracked stock against build output 2
        self.allocate_stock(
            self.output_2,
            {
                self.stock_3_1: 1,
            }
        )

        self.assertFalse(self.build.isFullyAllocated(self.output_2))

        # Partially allocate untracked stock against build
        self.allocate_stock(
            None,
            {
                self.stock_1_1: 1,
                self.stock_2_1: 1
            }
        )

        self.assertFalse(self.build.isFullyAllocated(None, verbose=True))

        unallocated = self.build.unallocatedParts(None)

        self.assertEqual(len(unallocated), 2)

        self.allocate_stock(
            None,
            {
                self.stock_1_2: 100,
            }
        )

        self.assertFalse(self.build.isFullyAllocated(None, verbose=True))

        unallocated = self.build.unallocatedParts(None)

        self.assertEqual(len(unallocated), 1)

        self.build.unallocateStock()

        unallocated = self.build.unallocatedParts(None)

        self.assertEqual(len(unallocated), 2)

        self.assertFalse(self.build.areUntrackedPartsFullyAllocated())

        # Now we "fully" allocate the untracked untracked items
        self.allocate_stock(
            None,
            {
                self.stock_1_1: 50,
                self.stock_2_1: 50,
            }
        )

        self.assertTrue(self.build.areUntrackedPartsFullyAllocated())

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

        # Allocate non-tracked parts
        self.allocate_stock(
            None,
            {
                self.stock_1_1: self.stock_1_1.quantity,  # Allocate *all* stock from this item
                self.stock_1_2: 10,
                self.stock_2_1: 30
            }
        )

        # Allocate tracked parts to output_1
        self.allocate_stock(
            self.output_1,
            {
                self.stock_3_1: 6
            }
        )

        # Allocate tracked parts to output_2
        self.allocate_stock(
            self.output_2,
            {
                self.stock_3_1: 14
            }
        )

        self.assertTrue(self.build.isFullyAllocated(None, verbose=True))
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

        self.assertEqual(StockItem.objects.count(), 8)

        # Clean up old stock items
        delete_old_stock_items()

        # New stock items should have been created!
        self.assertEqual(StockItem.objects.count(), 7)

        # This stock item has been depleted!
        with self.assertRaises(StockItem.DoesNotExist):
            StockItem.objects.get(pk=self.stock_1_1.pk)

        # This stock item has *not* been depleted
        x = StockItem.objects.get(pk=self.stock_2_1.pk)

        self.assertEqual(x.quantity, 4970)

        # And 10 new stock items created for the build output
        outputs = StockItem.objects.filter(build=self.build)

        self.assertEqual(outputs.count(), 2)

        for output in outputs:
            self.assertFalse(output.is_building)
