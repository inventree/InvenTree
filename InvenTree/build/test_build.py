"""Unit tests for the 'build' models"""

from django.test import TestCase

from django.core.exceptions import ValidationError

from InvenTree import status_codes as status

from build.models import Build, BuildItem, get_next_build_number
from part.models import Part, BomItem, BomItemSubstitute
from stock.models import StockItem


class BuildTestBase(TestCase):
    """Run some tests to ensure that the Build model is working properly."""

    def setUp(self):
        """Initialize data to use for these tests.

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
        self.bom_item_1 = BomItem.objects.create(
            part=self.assembly,
            sub_part=self.sub_part_1,
            quantity=5
        )

        self.bom_item_2 = BomItem.objects.create(
            part=self.assembly,
            sub_part=self.sub_part_2,
            quantity=3
        )

        # sub_part_3 is trackable!
        self.bom_item_3 = BomItem.objects.create(
            part=self.assembly,
            sub_part=self.sub_part_3,
            quantity=2
        )

        ref = get_next_build_number()

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
        self.stock_1_1 = StockItem.objects.create(part=self.sub_part_1, quantity=3)
        self.stock_1_2 = StockItem.objects.create(part=self.sub_part_1, quantity=100)

        self.stock_2_1 = StockItem.objects.create(part=self.sub_part_2, quantity=5)
        self.stock_2_2 = StockItem.objects.create(part=self.sub_part_2, quantity=5)
        self.stock_2_2 = StockItem.objects.create(part=self.sub_part_2, quantity=5)
        self.stock_2_2 = StockItem.objects.create(part=self.sub_part_2, quantity=5)
        self.stock_2_2 = StockItem.objects.create(part=self.sub_part_2, quantity=5)

        self.stock_3_1 = StockItem.objects.create(part=self.sub_part_3, quantity=1000)


class BuildTest(BuildTestBase):
    """Unit testing class for the Build model"""

    def test_ref_int(self):
        """Test the "integer reference" field used for natural sorting"""

        for ii in range(10):
            build = Build(
                reference=f"{ii}_abcde",
                quantity=1,
                part=self.assembly,
                title="Making some parts"
            )

            self.assertEqual(build.reference_int, 0)

            build.save()

            # After saving, the integer reference should have been updated
            self.assertEqual(build.reference_int, ii)

    def test_init(self):
        """Perform some basic tests before we start the ball rolling"""

        self.assertEqual(StockItem.objects.count(), 10)

        # Build is PENDING
        self.assertEqual(self.build.status, status.BuildStatus.PENDING)

        # Build has two build outputs
        self.assertEqual(self.build.output_count, 2)

        # None of the build outputs have been completed
        for output in self.build.get_build_outputs().all():
            self.assertFalse(self.build.is_fully_allocated(output))

        self.assertFalse(self.build.is_bom_item_allocated(self.bom_item_1, self.output_1))
        self.assertFalse(self.build.is_bom_item_allocated(self.bom_item_2, self.output_2))

        self.assertEqual(self.build.unallocated_quantity(self.bom_item_1, self.output_1), 15)
        self.assertEqual(self.build.unallocated_quantity(self.bom_item_1, self.output_2), 35)
        self.assertEqual(self.build.unallocated_quantity(self.bom_item_2, self.output_1), 9)
        self.assertEqual(self.build.unallocated_quantity(self.bom_item_2, self.output_2), 21)

        self.assertFalse(self.build.is_complete)

    def test_build_item_clean(self):
        """Ensure that dodgy BuildItem objects cannot be created"""

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
        b = BuildItem(stock_item=self.stock_1_2, build=self.build, install_into=self.output_1, quantity=10)
        b.save()

    def test_duplicate_bom_line(self):
        """Try to add a duplicate BOM item - it should be allowed"""

        BomItem.objects.create(
            part=self.assembly,
            sub_part=self.sub_part_1,
            quantity=99
        )

    def allocate_stock(self, output, allocations):
        """Allocate stock to this build, against a particular output

        Args:
            output: StockItem object (or None)
            allocations: Map of {StockItem: quantity}
        """

        for item, quantity in allocations.items():
            BuildItem.objects.create(
                build=self.build,
                stock_item=item,
                quantity=quantity,
                install_into=output
            )

    def test_partial_allocation(self):
        """Test partial allocation of stock"""

        # Fully allocate tracked stock against build output 1
        self.allocate_stock(
            self.output_1,
            {
                self.stock_3_1: 6,
            }
        )

        self.assertTrue(self.build.is_fully_allocated(self.output_1))

        # Partially allocate tracked stock against build output 2
        self.allocate_stock(
            self.output_2,
            {
                self.stock_3_1: 1,
            }
        )

        self.assertFalse(self.build.is_fully_allocated(self.output_2))

        # Partially allocate untracked stock against build
        self.allocate_stock(
            None,
            {
                self.stock_1_1: 1,
                self.stock_2_1: 1
            }
        )

        self.assertFalse(self.build.is_fully_allocated(None))

        unallocated = self.build.unallocated_bom_items(None)

        self.assertEqual(len(unallocated), 2)

        self.allocate_stock(
            None,
            {
                self.stock_1_2: 100,
            }
        )

        self.assertFalse(self.build.is_fully_allocated(None))

        unallocated = self.build.unallocated_bom_items(None)

        self.assertEqual(len(unallocated), 1)

        self.build.unallocateStock()

        unallocated = self.build.unallocated_bom_items(None)

        self.assertEqual(len(unallocated), 2)

        self.assertFalse(self.build.are_untracked_parts_allocated())

        self.stock_2_1.quantity = 500
        self.stock_2_1.save()

        # Now we "fully" allocate the untracked untracked items
        self.allocate_stock(
            None,
            {
                self.stock_1_2: 50,
                self.stock_2_1: 50,
            }
        )

        self.assertTrue(self.build.are_untracked_parts_allocated())

    def test_cancel(self):
        """Test cancellation of the build"""

        # TODO

        """
        self.allocate_stock(50, 50, 200, self.output_1)
        self.build.cancel_build(None)

        self.assertEqual(BuildItem.objects.count(), 0)
        """
        pass

    def test_complete(self):
        """Test completion of a build output"""

        self.stock_1_1.quantity = 1000
        self.stock_1_1.save()

        self.stock_2_1.quantity = 30
        self.stock_2_1.save()

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

        self.assertTrue(self.build.is_fully_allocated(None))
        self.assertTrue(self.build.is_fully_allocated(self.output_1))
        self.assertTrue(self.build.is_fully_allocated(self.output_2))

        self.build.complete_build_output(self.output_1, None)

        self.assertFalse(self.build.can_complete)

        self.build.complete_build_output(self.output_2, None)

        self.assertTrue(self.build.can_complete)

        self.build.complete_build(None)

        self.assertEqual(self.build.status, status.BuildStatus.COMPLETE)

        # the original BuildItem objects should have been deleted!
        self.assertEqual(BuildItem.objects.count(), 0)

        # New stock items should have been created!
        self.assertEqual(StockItem.objects.count(), 10)

        # This stock item has been depleted!
        with self.assertRaises(StockItem.DoesNotExist):
            StockItem.objects.get(pk=self.stock_1_1.pk)

        # This stock item has also been depleted
        with self.assertRaises(StockItem.DoesNotExist):
            StockItem.objects.get(pk=self.stock_2_1.pk)

        # And 10 new stock items created for the build output
        outputs = StockItem.objects.filter(build=self.build)

        self.assertEqual(outputs.count(), 2)

        for output in outputs:
            self.assertFalse(output.is_building)


class AutoAllocationTests(BuildTestBase):
    """Tests for auto allocating stock against a build order"""

    def setUp(self):
        """Init routines for this unit test class"""
        super().setUp()

        # Add a "substitute" part for bom_item_2
        alt_part = Part.objects.create(
            name="alt part",
            description="An alternative part!",
            component=True,
        )

        BomItemSubstitute.objects.create(
            bom_item=self.bom_item_2,
            part=alt_part,
        )

        StockItem.objects.create(
            part=alt_part,
            quantity=500,
        )

    def test_auto_allocate(self):
        """Run the 'auto-allocate' function. What do we expect to happen?

        There are two "untracked" parts:
            - sub_part_1 (quantity 5 per BOM = 50 required total) / 103 in stock (2 items)
            - sub_part_2 (quantity 3 per BOM = 30 required total) / 25 in stock (5 items)

        A "fully auto" allocation should allocate *all* of these stock items to the build
        """

        # No build item allocations have been made against the build
        self.assertEqual(self.build.allocated_stock.count(), 0)

        self.assertFalse(self.build.are_untracked_parts_allocated())

        # Stock is not interchangeable, nothing will happen
        self.build.auto_allocate_stock(
            interchangeable=False,
            substitutes=False,
        )

        self.assertFalse(self.build.are_untracked_parts_allocated())

        self.assertEqual(self.build.allocated_stock.count(), 0)

        self.assertFalse(self.build.is_bom_item_allocated(self.bom_item_1))
        self.assertFalse(self.build.is_bom_item_allocated(self.bom_item_2))

        self.assertEqual(self.build.unallocated_quantity(self.bom_item_1), 50)
        self.assertEqual(self.build.unallocated_quantity(self.bom_item_2), 30)

        # This time we expect stock to be allocated!
        self.build.auto_allocate_stock(
            interchangeable=True,
            substitutes=False,
        )

        self.assertFalse(self.build.are_untracked_parts_allocated())

        self.assertEqual(self.build.allocated_stock.count(), 7)

        self.assertTrue(self.build.is_bom_item_allocated(self.bom_item_1))
        self.assertFalse(self.build.is_bom_item_allocated(self.bom_item_2))

        self.assertEqual(self.build.unallocated_quantity(self.bom_item_1), 0)
        self.assertEqual(self.build.unallocated_quantity(self.bom_item_2), 5)

        # This time, allow substitue parts to be used!
        self.build.auto_allocate_stock(
            interchangeable=True,
            substitutes=True,
        )

        # self.assertTrue(self.build.are_untracked_parts_allocated())

        # self.assertEqual(self.build.allocated_stock.count(), 8)
        self.assertEqual(self.build.unallocated_quantity(self.bom_item_1), 0)
        self.assertEqual(self.build.unallocated_quantity(self.bom_item_2), 0)

        self.assertTrue(self.build.is_bom_item_allocated(self.bom_item_1))
        self.assertTrue(self.build.is_bom_item_allocated(self.bom_item_2))

    def test_fully_auto(self):
        """We should be able to auto-allocate against a build in a single go"""

        self.build.auto_allocate_stock(
            interchangeable=True,
            substitutes=True
        )

        self.assertTrue(self.build.are_untracked_parts_allocated())

        self.assertEqual(self.build.unallocated_quantity(self.bom_item_1), 0)
        self.assertEqual(self.build.unallocated_quantity(self.bom_item_2), 0)
