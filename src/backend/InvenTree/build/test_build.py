"""Unit tests for the 'build' models."""

import uuid
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.test.utils import override_settings
from django.urls import reverse

import structlog

import build.tasks
import common.models
import company.models
from build.models import Build, BuildItem, BuildLine, generate_next_build_reference
from build.status_codes import BuildStatus
from common.settings import set_global_setting
from InvenTree import status_codes as status
from InvenTree.unit_test import (
    InvenTreeAPITestCase,
    InvenTreeTestCase,
    findOffloadedEvent,
)
from order.models import PurchaseOrder, PurchaseOrderLineItem
from part.models import BomItem, BomItemSubstitute, Part, PartTestTemplate
from stock.models import (
    StockItem,
    StockItemTestResult,
    StockItemTracking,
    StockLocation,
)
from stock.status_codes import StockStatus
from users.models import Owner

logger = structlog.get_logger('inventree')


class BuildTestBase(InvenTreeTestCase):
    """Run some tests to ensure that the Build model is working properly."""

    fixtures = ['users']

    @classmethod
    def setUpTestData(cls):
        """Initialize data to use for these tests.

        The base Part 'assembly' has a BOM consisting of three parts:

        - 5 x sub_part_1
        - 3 x sub_part_2
        - 2 x sub_part_3 (trackable)

        We will build 10x 'assembly' parts, in two build outputs:

        - 3 x output_1
        - 7 x output_2

        """
        super().setUpTestData()

        # Create a base "Part"
        cls.assembly = Part.objects.create(
            name='An assembled part',
            description='Why does it matter what my description is?',
            assembly=True,
            trackable=True,
            testable=True,
        )

        # create one build with one required test template
        cls.tested_part_with_required_test = Part.objects.create(
            name='Part having required tests',
            description='Why does it matter what my description is?',
            assembly=True,
            trackable=True,
            testable=True,
        )

        cls.test_template_required = PartTestTemplate.objects.create(
            part=cls.tested_part_with_required_test,
            test_name='Required test',
            description='Required test template description',
            required=True,
            requires_value=False,
            requires_attachment=False,
        )

        ref = generate_next_build_reference()

        cls.build_w_tests_trackable = Build.objects.create(
            reference=ref,
            title='This is a build',
            part=cls.tested_part_with_required_test,
            quantity=1,
            issued_by=get_user_model().objects.get(pk=1),
        )

        cls.stockitem_with_required_test = StockItem.objects.create(
            part=cls.tested_part_with_required_test,
            quantity=1,
            is_building=True,
            serial=uuid.uuid4(),
            build=cls.build_w_tests_trackable,
        )

        # now create a part with a non-required test template
        cls.tested_part_wo_required_test = Part.objects.create(
            name='Part with one non.required test',
            description='Why does it matter what my description is?',
            assembly=True,
            trackable=True,
            testable=True,
        )

        cls.test_template_non_required = PartTestTemplate.objects.create(
            part=cls.tested_part_wo_required_test,
            test_name='Required test template',
            description='Required test template description',
            required=False,
            requires_value=False,
            requires_attachment=False,
        )

        ref = generate_next_build_reference()

        cls.build_wo_tests_trackable = Build.objects.create(
            reference=ref,
            title='This is a build',
            part=cls.tested_part_wo_required_test,
            quantity=1,
            issued_by=get_user_model().objects.get(pk=1),
        )

        cls.stockitem_wo_required_test = StockItem.objects.create(
            part=cls.tested_part_wo_required_test,
            quantity=1,
            is_building=True,
            serial=uuid.uuid4(),
            build=cls.build_wo_tests_trackable,
        )

        cls.sub_part_1 = Part.objects.create(
            name='Widget A', description='A widget', component=True
        )

        cls.sub_part_2 = Part.objects.create(
            name='Widget B', description='A widget', component=True
        )

        cls.sub_part_3 = Part.objects.create(
            name='Widget C', description='A widget', component=True, trackable=True
        )

        # Create BOM item links for the parts
        cls.bom_item_1 = BomItem.objects.create(
            part=cls.assembly, sub_part=cls.sub_part_1, quantity=5
        )

        cls.bom_item_2 = BomItem.objects.create(
            part=cls.assembly, sub_part=cls.sub_part_2, quantity=3, optional=True
        )

        # sub_part_3 is trackable!
        cls.bom_item_3 = BomItem.objects.create(
            part=cls.assembly, sub_part=cls.sub_part_3, quantity=2
        )

        ref = generate_next_build_reference()

        # Create a "Build" object to make 10x objects
        cls.build = Build.objects.create(
            reference=ref,
            title='This is a build',
            part=cls.assembly,
            quantity=10,
            issued_by=get_user_model().objects.get(pk=1),
            status=BuildStatus.PENDING,
        )

        # Create some BuildLine items we can use later on
        cls.line_1 = BuildLine.objects.get(build=cls.build, bom_item=cls.bom_item_1)
        cls.line_2 = BuildLine.objects.get(build=cls.build, bom_item=cls.bom_item_2)
        cls.line_3 = BuildLine.objects.get(build=cls.build, bom_item=cls.bom_item_3)

        # Create some build output (StockItem) objects
        cls.output_1 = StockItem.objects.create(
            part=cls.assembly, quantity=3, is_building=True, build=cls.build
        )

        cls.output_2 = StockItem.objects.create(
            part=cls.assembly, quantity=7, is_building=True, build=cls.build
        )

        # Create some stock items to assign to the build
        cls.stock_1_1 = StockItem.objects.create(part=cls.sub_part_1, quantity=3)
        cls.stock_1_2 = StockItem.objects.create(part=cls.sub_part_1, quantity=100)

        cls.stock_2_1 = StockItem.objects.create(part=cls.sub_part_2, quantity=5)
        cls.stock_2_2 = StockItem.objects.create(part=cls.sub_part_2, quantity=5)
        cls.stock_2_3 = StockItem.objects.create(part=cls.sub_part_2, quantity=5)
        cls.stock_2_4 = StockItem.objects.create(part=cls.sub_part_2, quantity=5)
        cls.stock_2_5 = StockItem.objects.create(part=cls.sub_part_2, quantity=5)

        cls.stock_3_1 = StockItem.objects.create(part=cls.sub_part_3, quantity=1000)


class BuildTest(BuildTestBase):
    """Unit testing class for the Build model."""

    def test_ref_int(self):
        """Test the "integer reference" field used for natural sorting."""
        # Set build reference to new value
        set_global_setting(
            'BUILDORDER_REFERENCE_PATTERN', 'BO-{ref}-???', change_user=None
        )

        refs = {
            'BO-123-456': 123,
            'BO-456-123': 456,
            'BO-999-ABC': 999,
            'BO-123ABC-ABC': 123,
            'BO-ABC123-ABC': 123,
        }

        for ref, ref_int in refs.items():
            build = Build(
                reference=ref, quantity=1, part=self.assembly, title='Making some parts'
            )

            self.assertEqual(build.reference_int, 0)
            build.save()
            self.assertEqual(build.reference_int, ref_int)

        # Set build reference back to default value
        set_global_setting(
            'BUILDORDER_REFERENCE_PATTERN',
            'BO-{ref:04d}',  # noqa: RUF027
            change_user=None,
        )

    def test_ref_validation(self):
        """Test that the reference field validation works as expected."""
        # Default reference pattern = 'BO-{ref:04d}
        # These patterns should fail
        for ref in ['BO-1234x', 'BO1234', 'OB-1234', 'BO--1234']:
            with self.assertRaises(ValidationError):
                Build.objects.create(
                    part=self.assembly,
                    quantity=10,
                    reference=ref,
                    title='Invalid reference',
                )

        for ref in ['BO-1234', 'BO-9999', 'BO-123']:
            Build.objects.create(
                part=self.assembly, quantity=10, reference=ref, title='Valid reference'
            )

        # Try a new validator pattern
        set_global_setting('BUILDORDER_REFERENCE_PATTERN', '{ref}-BO', change_user=None)  # noqa: RUF027

        for ref in ['1234-BO', '9999-BO']:
            Build.objects.create(
                part=self.assembly, quantity=10, reference=ref, title='Valid reference'
            )

        # Set build reference back to default value
        set_global_setting(
            'BUILDORDER_REFERENCE_PATTERN',
            'BO-{ref:04d}',  # noqa: RUF027
            change_user=None,
        )

    def test_next_ref(self):
        """Test that the next reference is automatically generated."""
        set_global_setting(
            'BUILDORDER_REFERENCE_PATTERN', 'XYZ-{ref:06d}', change_user=None
        )

        build = Build.objects.create(
            part=self.assembly, quantity=5, reference='XYZ-987', title='Some thing'
        )

        self.assertEqual(build.reference_int, 987)

        # Now create one *without* specifying the reference
        build = Build.objects.create(
            part=self.assembly, quantity=1, title='Some new title'
        )

        self.assertEqual(build.reference, 'XYZ-000988')
        self.assertEqual(build.reference_int, 988)

        # Set build reference back to default value
        set_global_setting(
            'BUILDORDER_REFERENCE_PATTERN', 'BO-{ref:04d}', change_user=None
        )

    def test_init(self):
        """Perform some basic tests before we start the ball rolling."""
        self.assertEqual(StockItem.objects.count(), 12)

        # Build is PENDING
        self.assertEqual(self.build.status, status.BuildStatus.PENDING)

        self.assertTrue(self.build.is_active)
        self.assertTrue(self.build.can_hold)
        self.assertTrue(self.build.can_issue)

        # Build has two build outputs
        self.assertEqual(self.build.output_count, 2)

        # None of the build outputs have been completed
        for output in self.build.get_build_outputs().all():
            self.assertFalse(self.build.is_fully_allocated(output))

        self.assertFalse(self.line_1.is_fully_allocated())
        self.assertFalse(self.line_2.is_overallocated())

        self.assertEqual(self.line_1.allocated_quantity(), 0)

        self.assertFalse(self.build.is_complete)

    def test_build_item_clean(self):
        """Ensure that dodgy BuildItem objects cannot be created."""
        stock = StockItem.objects.create(part=self.assembly, quantity=99)

        # Create a BuiltItem which points to an invalid StockItem
        b = BuildItem(stock_item=stock, build_line=self.line_2, quantity=10)

        with self.assertRaises(ValidationError):
            b.save()

        # Create a BuildItem which has too much stock assigned
        b = BuildItem(
            stock_item=self.stock_1_1, build_line=self.line_1, quantity=9999999
        )

        with self.assertRaises(ValidationError):
            b.clean()

        # Negative stock? Not on my watch!
        b = BuildItem(stock_item=self.stock_1_1, build_line=self.line_1, quantity=-99)

        with self.assertRaises(ValidationError):
            b.clean()

        # Ok, what about we make one that does *not* fail?
        b = BuildItem(
            stock_item=self.stock_1_2,
            build_line=self.line_1,
            install_into=self.output_1,
            quantity=10,
        )
        b.save()

    def test_duplicate_bom_line(self):
        """Try to add a duplicate BOM item - it should be allowed."""
        BomItem.objects.create(
            part=self.assembly, sub_part=self.sub_part_1, quantity=99
        )

    def allocate_stock(self, output, allocations):
        """Allocate stock to this build, against a particular output.

        Args:
            output: StockItem object (or None)
            allocations: Map of {StockItem: quantity}
        """
        items_to_create = []

        for item, quantity in allocations.items():
            # Find an appropriate BuildLine to allocate against
            line = BuildLine.objects.filter(
                build=self.build, bom_item__sub_part=item.part
            ).first()

            items_to_create.append(
                BuildItem(
                    build_line=line,
                    stock_item=item,
                    quantity=quantity,
                    install_into=output,
                )
            )

        BuildItem.objects.bulk_create(items_to_create)

    def test_partial_allocation(self):
        """Test partial allocation of stock."""
        # Fully allocate tracked stock against build output 1
        self.allocate_stock(self.output_1, {self.stock_3_1: 6})

        self.assertTrue(self.build.is_output_fully_allocated(self.output_1))

        # Partially allocate tracked stock against build output 2
        self.allocate_stock(self.output_2, {self.stock_3_1: 1})

        self.assertFalse(self.build.is_output_fully_allocated(self.output_2))

        # Partially allocate untracked stock against build
        self.allocate_stock(None, {self.stock_1_1: 1, self.stock_2_1: 1})

        self.assertFalse(self.build.is_output_fully_allocated(None))

        # Find lines which are *not* fully allocated
        unallocated = self.build.unallocated_lines()

        self.assertEqual(len(unallocated), 3)

        self.allocate_stock(None, {self.stock_1_2: 100})

        self.assertFalse(self.build.is_fully_allocated(None))

        unallocated = self.build.unallocated_lines()

        self.assertEqual(len(unallocated), 2)

        self.build.deallocate_stock()

        unallocated = self.build.unallocated_lines(None)

        self.assertEqual(len(unallocated), 3)

        self.assertFalse(self.build.is_fully_allocated(tracked=False))

        self.stock_2_1.quantity = 500
        self.stock_2_1.save()

        # Now we "fully" allocate the untracked untracked items
        self.allocate_stock(None, {self.stock_1_2: 50, self.stock_2_1: 50})

        self.assertTrue(self.build.is_fully_allocated(tracked=False))

    def test_overallocation_and_trim(self):
        """Test overallocation of stock and trim function."""
        self.assertEqual(self.build.status, status.BuildStatus.PENDING)
        self.build.issue_build()
        self.assertEqual(self.build.status, status.BuildStatus.PRODUCTION)

        # Fully allocate tracked stock (not eligible for trimming)
        self.allocate_stock(self.output_1, {self.stock_3_1: 6})
        self.allocate_stock(self.output_2, {self.stock_3_1: 14})
        # Fully allocate part 1 (should be left alone)
        self.allocate_stock(None, {self.stock_1_1: 3, self.stock_1_2: 47})

        extra_2_1 = StockItem.objects.create(part=self.sub_part_2, quantity=6)
        extra_2_2 = StockItem.objects.create(part=self.sub_part_2, quantity=4)

        # Overallocate part 2 (30 needed)
        self.allocate_stock(
            None,
            {
                self.stock_2_1: 5,
                self.stock_2_2: 5,
                self.stock_2_3: 5,
                self.stock_2_4: 5,
                self.stock_2_5: 5,  # 25
                extra_2_1: 6,  # 31
                extra_2_2: 4,  # 35
            },
        )

        self.assertTrue(self.build.is_overallocated())

        self.build.trim_allocated_stock()
        self.assertFalse(self.build.is_overallocated())

        self.build.complete_build_output(self.output_1, None)
        self.build.complete_build_output(self.output_2, None)

        self.assertTrue(self.build.can_complete)

        n = StockItem.objects.filter(consumed_by=self.build).count()

        self.build.complete_build(None)

        self.assertEqual(self.build.status, status.BuildStatus.COMPLETE)

        # Check stock items are in expected state.
        self.assertEqual(StockItem.objects.get(pk=self.stock_1_2.pk).quantity, 53)

        # Total stock quantity has not been decreased
        items = StockItem.objects.filter(part=self.sub_part_2)
        self.assertEqual(items.aggregate(Sum('quantity'))['quantity__sum'], 35)

        # However, the "available" stock quantity has been decreased
        self.assertEqual(
            items.filter(consumed_by=None).aggregate(Sum('quantity'))['quantity__sum'],
            5,
        )

        # And the "consumed_by" quantity has been increased
        self.assertEqual(
            items.filter(consumed_by=self.build).aggregate(Sum('quantity'))[
                'quantity__sum'
            ],
            30,
        )

        self.assertEqual(StockItem.objects.get(pk=self.stock_3_1.pk).quantity, 980)

        # Check that the "consumed_by" item count has increased
        consumed_items = StockItem.objects.filter(consumed_by=self.build)
        self.assertEqual(consumed_items.count(), n + 8)

        # Finally, return the items into stock
        location = StockLocation.objects.filter(structural=False).first()

        for item in consumed_items:
            item.return_to_stock(location)

        # No consumed items should remain
        self.assertEqual(StockItem.objects.filter(consumed_by=self.build).count(), 0)

    def test_return_consumed(self):
        """Test returning consumed stock items to stock."""
        self.build.auto_allocate_stock(interchangeable=True)

        self.build.incomplete_outputs.delete()

        self.assertGreater(self.build.allocated_stock.count(), 0)

        self.build.complete_build(self.user)
        consumed_items = StockItem.objects.filter(consumed_by=self.build)
        self.assertGreater(consumed_items.count(), 0)

        location = StockLocation.objects.filter(structural=False).last()

        # Return a partial quantity of each item to stock
        for item in consumed_items:
            q = item.quantity
            self.assertGreater(item.quantity, 1)
            item.return_to_stock(location, merge=False, quantity=1)
            item.refresh_from_db()
            self.assertEqual(item.quantity, q - 1)
            self.assertEqual(item.children.count(), 1)
            self.assertFalse(item.is_in_stock())
            child = item.children.first()
            self.assertTrue(child.is_in_stock())

    def test_change_part(self):
        """Try to change target part after creating a build."""
        bo = Build.objects.create(
            reference='BO-9999',
            title='Some new build',
            part=self.assembly,
            quantity=5,
            issued_by=get_user_model().objects.get(pk=1),
        )

        assembly_2 = Part.objects.create(
            name='Another assembly', description='A different assembly', assembly=True
        )

        # Should not be able to change the part after the Build is saved
        with self.assertRaises(ValidationError):
            bo.part = assembly_2
            bo.clean()

    def test_cancel(self):
        """Test build cancellation: status is updated and allocations are removed by default."""
        self.build.issue_build()

        self.allocate_stock(None, {self.stock_1_2: 50})
        self.assertGreater(self.build.allocated_stock.count(), 0)

        initial_output_count = self.build.build_outputs.filter(is_building=True).count()
        self.assertGreater(initial_output_count, 0)

        self.build.cancel_build(None)
        self.build.refresh_from_db()

        self.assertEqual(self.build.status, BuildStatus.CANCELLED)

        # Allocations removed (but stock not consumed) by default
        self.assertEqual(self.build.allocated_stock.count(), 0)
        self.assertIsNone(StockItem.objects.get(pk=self.stock_1_2.pk).consumed_by)

        # Incomplete outputs preserved by default (remove_incomplete_outputs=False)
        self.assertEqual(
            self.build.build_outputs.filter(is_building=True).count(),
            initial_output_count,
        )

    def test_complete(self):
        """Test completion of a build output."""
        self.stock_1_1.quantity = 1000
        self.stock_1_1.save()

        self.stock_2_1.quantity = 30
        self.stock_2_1.save()

        self.build.issue_build()

        # Allocate non-tracked parts
        self.allocate_stock(
            None,
            {
                self.stock_1_1: self.stock_1_1.quantity,  # Allocate *all* stock from this item
                self.stock_1_2: 10,
                self.stock_2_1: 30,
            },
        )

        # Allocate tracked parts to output_1
        self.allocate_stock(self.output_1, {self.stock_3_1: 6})

        # Allocate tracked parts to output_2
        self.allocate_stock(self.output_2, {self.stock_3_1: 14})

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
        self.assertEqual(StockItem.objects.count(), 15)

        # This stock item has been marked as "consumed"
        item = StockItem.objects.get(pk=self.stock_1_1.pk)
        self.assertIsNotNone(item.consumed_by)
        self.assertFalse(item.in_stock)

        # And 10 new stock items created for the build output
        outputs = StockItem.objects.filter(build=self.build)

        self.assertEqual(outputs.count(), 2)

        for output in outputs:
            self.assertFalse(output.is_building)

    def test_complete_output_stale_build_instance(self):
        """The 'completed' count is incremented atomically at the database level.

        Simulates two concurrent processes completing different outputs of the
        same build, each holding its own (stale) copy of the Build instance.
        """
        self.stock_1_1.quantity = 1000
        self.stock_1_1.save()

        self.stock_2_1.quantity = 30
        self.stock_2_1.save()

        self.build.issue_build()

        # Allocate non-tracked parts
        self.allocate_stock(
            None,
            {
                self.stock_1_1: self.stock_1_1.quantity,
                self.stock_1_2: 10,
                self.stock_2_1: 30,
            },
        )

        # Allocate tracked parts against each output
        self.allocate_stock(self.output_1, {self.stock_3_1: 6})
        self.allocate_stock(self.output_2, {self.stock_3_1: 14})

        # Two independent in-memory copies of the same build
        build_a = Build.objects.get(pk=self.build.pk)
        build_b = Build.objects.get(pk=self.build.pk)

        build_a.complete_build_output(self.output_1, None)
        build_b.complete_build_output(self.output_2, None)

        # Both completions must be counted
        self.build.refresh_from_db()
        self.assertEqual(self.build.completed, 10)

    def test_complete_allocation_stale_build_line(self):
        """The 'consumed' count is incremented atomically at the database level.

        Simulates two concurrent workers completing different allocations
        against the same BuildLine, each holding its own (stale) copy of the line.
        """
        self.build.issue_build()

        self.allocate_stock(None, {self.stock_1_1: 3, self.stock_1_2: 5})

        alloc_a, alloc_b = BuildItem.objects.filter(build_line=self.line_1).order_by(
            'pk'
        )

        # Cache a separate copy of the BuildLine on each allocation
        self.assertEqual(alloc_a.build_line.consumed, 0)
        self.assertEqual(alloc_b.build_line.consumed, 0)

        alloc_a.complete_allocation(user=self.user)
        alloc_b.complete_allocation(user=self.user)

        # Both consumed quantities must be counted
        self.line_1.refresh_from_db()
        self.assertEqual(self.line_1.consumed, 8)

    def test_complete_with_required_tests(self):
        """Test the prevention completion when a required test is missing feature."""
        # with required tests incompleted the save should fail
        set_global_setting(
            'PREVENT_BUILD_COMPLETION_HAVING_INCOMPLETED_TESTS', True, change_user=None
        )

        with self.assertRaises(ValidationError) as exc:
            self.build_w_tests_trackable.complete_build_output(
                self.stockitem_with_required_test, None
            )

        self.assertIn(
            'Build output has not passed all required tests', str(exc.exception)
        )

        # let's complete the required test and see if it could be saved
        StockItemTestResult.objects.create(
            stock_item=self.stockitem_with_required_test,
            template=self.test_template_required,
            result=True,
        )

        self.build_w_tests_trackable.complete_build_output(
            self.stockitem_with_required_test, None
        )

        # let's see if a non required test could be saved
        self.build_wo_tests_trackable.complete_build_output(
            self.stockitem_wo_required_test, None
        )

    def test_complete_output_still_in_production(self):
        """Test that a build output cannot be completed if allocated stock is still in production."""
        # Create a stock item of the tracked sub-part, which is itself still "in production"
        sub_build = Build.objects.create(
            reference=generate_next_build_reference(),
            title='Building a sub-part',
            part=self.sub_part_3,
            quantity=2,
            issued_by=get_user_model().objects.get(pk=1),
        )

        in_production = StockItem.objects.create(
            part=self.sub_part_3, quantity=2, is_building=True, build=sub_build
        )

        self.allocate_stock(self.output_1, {in_production: 2})

        with self.assertRaises(ValidationError) as exc:
            self.build.complete_build_output(self.output_1, None)

        self.assertIn(
            'Allocated stock items are still in production', str(exc.exception)
        )

    def test_partial_complete_with_allocated_items(self):
        """Test that a build output with tracked allocations cannot be partially completed."""
        # Allocate tracked stock against output_1 (quantity=3)
        self.allocate_stock(self.output_1, {self.stock_3_1: 6})

        with self.assertRaises(ValidationError) as exc:
            self.build.complete_build_output(self.output_1, None, quantity=1)

        self.assertIn(
            'Cannot partially complete a build output with allocated items',
            str(exc.exception),
        )

    def test_complete_output_invalid_quantity(self):
        """Test that invalid quantities are rejected when completing a build output directly."""
        with self.assertRaises(ValidationError) as exc:
            self.build.complete_build_output(self.output_1, None, quantity=0)

        self.assertIn('Quantity must be greater than zero', str(exc.exception))

        with self.assertRaises(ValidationError) as exc:
            self.build.complete_build_output(
                self.output_1, None, quantity=self.output_1.quantity + 1
            )

        self.assertIn(
            'Quantity cannot be greater than the output quantity', str(exc.exception)
        )

    def test_overdue_notification(self):
        """Test sending of notifications when a build order is overdue."""
        self.ensurePluginsLoaded()

        self.build.target_date = datetime.now().date() - timedelta(days=1)
        self.build.save()

        # Check for overdue orders
        build.tasks.check_overdue_build_orders()

        message = common.models.NotificationMessage.objects.get(
            category='build.overdue_build_order', user__id=1
        )

        self.assertEqual(message.name, 'Overdue Build Order')

    def test_new_build_notification(self):
        """Test that a notification is sent when a new build is created."""
        Build.objects.create(
            reference='BO-9999',
            title='Some new build',
            part=self.assembly,
            quantity=5,
            issued_by=get_user_model().objects.get(pk=2),
            responsible=Owner.create(obj=Group.objects.get(pk=3)),
        )

        # Two notifications should have been sent
        messages = common.models.NotificationMessage.objects.filter(
            category='build.new_build'
        )

        self.assertEqual(messages.count(), 1)

        self.assertFalse(messages.filter(user__pk=2).exists())

        # Inactive users do not receive notifications
        self.assertFalse(messages.filter(user__pk=3).exists())

        self.assertTrue(messages.filter(user__pk=4).exists())

    @override_settings(
        TESTING_TABLE_EVENTS=True,
        PLUGIN_TESTING_EVENTS=True,
        PLUGIN_TESTING_EVENTS_ASYNC=True,
    )
    def test_events(self):
        """Test that build events are triggered correctly."""
        from django_q.models import OrmQ

        from build.events import BuildEvents

        set_global_setting('ENABLE_PLUGINS_EVENTS', True)

        OrmQ.objects.all().delete()

        # Create a new build
        build = Build.objects.create(
            reference='BO-9999',
            title='Some new build',
            part=self.assembly,
            quantity=5,
            issued_by=get_user_model().objects.get(pk=2),
            responsible=Owner.create(obj=Group.objects.get(pk=3)),
        )

        # Check that the 'build.created' event was triggered
        task = findOffloadedEvent(
            'build_build.created',
            matching_kwargs=['id', 'model'],
            reverse=True,
            clear_after=True,
        )

        # Assert that the task was found
        self.assertIsNotNone(task)

        # Check that the Build ID matches
        self.assertEqual(task.kwargs()['id'], build.pk)

        # Issue the build
        build.issue_build()

        # Check that the 'build.issued' event was triggered
        task = findOffloadedEvent(
            BuildEvents.ISSUED, matching_kwargs=['id'], clear_after=True
        )

        self.assertIsNotNone(task)

        set_global_setting('ENABLE_PLUGINS_EVENTS', False)

    def test_metadata(self):
        """Unit tests for the metadata field."""
        # Make sure a BuildItem exists before trying to run this test
        b = BuildItem(
            stock_item=self.stock_1_2,
            build_line=self.line_1,
            install_into=self.output_1,
            quantity=10,
        )
        b.save()

        for model in [Build, BuildItem]:
            p = model.objects.first()
            self.assertEqual(len(p.metadata.keys()), 0)

            self.assertIsNone(p.get_metadata('test'))
            self.assertEqual(p.get_metadata('test', backup_value=123), 123)

            # Test update via the set_metadata() method
            p.set_metadata('test', 3)
            self.assertEqual(p.get_metadata('test'), 3)

            for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
                p.set_metadata(k, k)

            self.assertEqual(len(p.metadata.keys()), 4)


class AutoAllocationTests(BuildTestBase):
    """Tests for auto allocating stock against a build order."""

    def setUp(self):
        """Init routines for this unit test class."""
        super().setUp()

        # Add a "substitute" part for bom_item_2
        alt_part = Part.objects.create(
            name='alt part', description='An alternative part!', component=True
        )

        BomItemSubstitute.objects.create(bom_item=self.bom_item_2, part=alt_part)

        StockItem.objects.create(part=alt_part, quantity=500)

    def test_auto_allocate(self):
        """Run the 'auto-allocate' function. What do we expect to happen?

        There are two "untracked" parts:
            - sub_part_1 (quantity 5 per BOM = 50 required total) / 103 in stock (2 items)
            - sub_part_2 (quantity 3 per BOM = 30 required total) / 25 in stock (5 items)

        A "fully auto" allocation should allocate *all* of these stock items to the build
        """
        # No build item allocations have been made against the build
        self.assertEqual(self.build.allocated_stock.count(), 0)

        self.assertFalse(self.build.is_fully_allocated(tracked=False))

        # Stock is not interchangeable, nothing will happen
        self.build.auto_allocate_stock(interchangeable=False, substitutes=False)

        self.assertFalse(self.build.is_fully_allocated(tracked=False))

        self.assertEqual(self.build.allocated_stock.count(), 0)

        self.assertFalse(self.line_1.is_fully_allocated())
        self.assertFalse(self.line_2.is_fully_allocated())

        self.assertEqual(self.line_1.unallocated_quantity(), 50)
        self.assertEqual(self.line_2.unallocated_quantity(), 30)

        # This time we expect stock to be allocated!
        self.build.auto_allocate_stock(
            interchangeable=True, substitutes=False, optional_items=True
        )

        self.assertFalse(self.build.is_fully_allocated(tracked=False))

        self.assertEqual(self.build.allocated_stock.count(), 7)

        self.assertTrue(self.line_1.is_fully_allocated())
        self.assertFalse(self.line_2.is_fully_allocated())

        self.assertEqual(self.line_1.unallocated_quantity(), 0)
        self.assertEqual(self.line_2.unallocated_quantity(), 5)

        # This time, allow substitute parts to be used!
        self.build.auto_allocate_stock(interchangeable=True, substitutes=True)

        self.assertEqual(self.line_1.unallocated_quantity(), 0)
        self.assertEqual(self.line_2.unallocated_quantity(), 5)

        self.assertTrue(self.line_1.is_fully_allocated())
        self.assertFalse(self.line_2.is_fully_allocated())

    def test_fully_auto(self):
        """We should be able to auto-allocate against a build in a single go."""
        self.build.auto_allocate_stock(
            interchangeable=True, substitutes=True, optional_items=True
        )

        self.assertTrue(self.build.is_fully_allocated(tracked=False))

        self.assertEqual(self.line_1.unallocated_quantity(), 0)
        self.assertEqual(self.line_2.unallocated_quantity(), 0)

    def test_allocate_consumed(self):
        """Test for auto-allocation against a build which has been fully consumed.

        Steps:
            1. Fully allocate the build (using the auto-allocate function)
            2. Consume allocated stock
            3. Ensure that all allocations are removed
            4. Re-run the auto-allocate function
            5. Check that no new allocations have been made
        """
        self.assertEqual(self.build.allocated_stock.count(), 0)
        self.assertFalse(self.build.is_fully_allocated(tracked=False))

        # Auto allocate stock against the build order
        self.build.auto_allocate_stock(
            interchangeable=True, substitutes=True, optional_items=True
        )

        self.assertEqual(self.line_1.allocated_quantity(), 50)
        self.assertEqual(self.line_2.allocated_quantity(), 30)

        self.assertEqual(self.line_1.unallocated_quantity(), 0)
        self.assertEqual(self.line_2.unallocated_quantity(), 0)

        self.assertTrue(self.line_1.is_fully_allocated())
        self.assertTrue(self.line_2.is_fully_allocated())

        self.assertFalse(self.line_1.is_overallocated())
        self.assertFalse(self.line_2.is_overallocated())

        N = self.build.allocated_stock.count()

        self.assertEqual(self.line_1.allocations.count(), 2)
        self.assertEqual(self.line_2.allocations.count(), 6)

        for item in self.line_1.allocations.all():
            item.complete_allocation()

        for item in self.line_2.allocations.all():
            item.complete_allocation()

        self.line_1.refresh_from_db()
        self.line_2.refresh_from_db()

        self.assertTrue(self.line_1.is_fully_allocated())
        self.assertTrue(self.line_2.is_fully_allocated())
        self.assertFalse(self.line_1.is_overallocated())
        self.assertFalse(self.line_2.is_overallocated())

        self.assertEqual(self.line_1.allocations.count(), 0)
        self.assertEqual(self.line_2.allocations.count(), 0)

        self.assertEqual(self.line_1.quantity, self.line_1.consumed)
        self.assertEqual(self.line_2.quantity, self.line_2.consumed)

        # Check that the "allocations" have been removed
        self.assertEqual(self.build.allocated_stock.count(), N - 8)

        # Now, try to auto-allocate again
        self.build.auto_allocate_stock(
            interchangeable=True, substitutes=True, optional_items=True
        )

        # Ensure that there are no "new" allocations (there should be none!)
        self.assertEqual(self.line_1.allocated_quantity(), 0)
        self.assertEqual(self.line_2.allocated_quantity(), 0)

        self.assertEqual(self.line_1.unallocated_quantity(), 0)
        self.assertEqual(self.line_2.unallocated_quantity(), 0)

        self.assertEqual(self.build.allocated_stock.count(), N - 8)

    def test_consumable_via_part(self):
        """A BOM line should be treated as consumable if the underlying part is consumable.

        Even though 'bom_item_1' itself is not marked as consumable, marking
        'sub_part_1' as consumable should have the same effect as marking the
        BOM line itself as consumable.
        """
        self.sub_part_1.consumable = True
        self.sub_part_1.save()

        self.assertFalse(self.bom_item_1.consumable)
        self.assertTrue(self.bom_item_1.is_consumable)

        # The BuildLine should be treated as fully allocated, without any stock allocated
        self.assertEqual(self.line_1.allocated_quantity(), 0)
        self.assertTrue(self.line_1.is_fully_allocated())

        # The build should not consider this line when checking for unallocated lines
        unallocated_lines = self.build.unallocated_lines(tracked=False)
        self.assertNotIn(self.line_1, unallocated_lines)

        # Auto-allocation should skip this line, even though stock exists
        self.build.auto_allocate_stock(
            interchangeable=True, substitutes=True, optional_items=True
        )

        self.assertEqual(self.line_1.allocated_quantity(), 0)
        self.assertEqual(BuildItem.objects.filter(build_line=self.line_1).count(), 0)

        # The other (non-consumable) line should still be allocated as normal
        self.assertEqual(self.line_2.allocated_quantity(), 30)


class ExternalBuildTest(InvenTreeAPITestCase):
    """Unit tests for external build order functionality."""

    def test_validation(self):
        """Test validation of external build logic."""
        part = Part.objects.create(
            name='Test part',
            description='A test part',
            assembly=True,
            purchaseable=False,
        )

        # Create a build order
        # Cannot create an external build for a non-purchaseable part
        with self.assertRaises(ValidationError) as err:
            build = Build.objects.create(
                part=part, title='Test build order', quantity=10, external=True
            )

            build.clean()

        self.assertIn(
            'Build orders can only be externally fulfilled for purchaseable parts',
            str(err.exception.messages),
        )

    def test_build_requirement(self):
        """Test the global 'BUILDORDER_EXTERNAL_REQUIRED' setting."""
        # Create required test data
        part = Part.objects.create(
            name='Test part',
            description='A test part',
            assembly=True,
            purchaseable=True,
        )
        supplier = company.models.Company.objects.create(
            name='Test supplier', active=True, is_supplier=True
        )
        supplier_part = company.models.SupplierPart.objects.create(
            part=part, supplier=supplier, SKU='TEST-123'
        )

        po = PurchaseOrder.objects.create(supplier=supplier, reference='PO-9999')
        po_line = PurchaseOrderLineItem.objects.create(
            order=po, part=supplier_part, quantity=10
        )

        set_global_setting('BUILDORDER_EXTERNAL_REQUIRED', False)
        po_line.clean()  # Should not raise an error

        set_global_setting('BUILDORDER_EXTERNAL_BUILDS', True)
        set_global_setting('BUILDORDER_EXTERNAL_REQUIRED', True)

        # Expect failure, there is no linked build order
        with self.assertRaises(ValidationError):
            po_line.clean()

        # Create and link a build order
        build = Build.objects.create(
            part=part, title='Test build order', quantity=10, external=True
        )
        po_line.build_order = build
        po_line.save()

        # Clean step now passes
        po_line.clean()

    def test_logic(self):
        """Test external build logic."""
        # Create a purchaseable assembly part
        assembly = Part.objects.create(
            name='Test assembly',
            description='A test assembly',
            purchaseable=True,
            assembly=True,
            active=True,
        )

        # Create a supplier part
        supplier = company.models.Company.objects.create(
            name='Test supplier', active=True, is_supplier=True
        )

        supplier_part = company.models.SupplierPart.objects.create(
            part=assembly, supplier=supplier, SKU='TEST-123'
        )

        # Create a build order against the assembly
        build = Build.objects.create(
            part=assembly, title='Test build order', quantity=10, external=True
        )

        # Order some parts
        po = PurchaseOrder.objects.create(supplier=supplier, reference='PO-9999')

        # Create a line item to fulfil the build order
        po_line = PurchaseOrderLineItem.objects.create(
            order=po, part=supplier_part, quantity=10, build_order=build
        )

        # Validate starting conditions
        self.assertEqual(build.quantity, 10)
        self.assertEqual(build.completed, 0)
        self.assertEqual(build.build_outputs.count(), 0)
        self.assertEqual(build.consumed_stock.count(), 0)

        # PLACE the order
        po.place_order()

        location = StockLocation.objects.first()

        # Receive half the items against the purchase order
        po.receive_line_item(po_line, location, 5, self.user)

        # As the order was incomplete, the build output has been marked as "building"
        self.assertEqual(build.quantity, 10)
        self.assertEqual(build.completed, 0)
        self.assertEqual(build.build_outputs.count(), 1)

        output = build.build_outputs.first()
        self.assertTrue(output.is_building)

        build.complete_build_output(output, self.user)
        build.refresh_from_db()
        self.assertEqual(build.completed, 5)

        output.refresh_from_db()
        self.assertFalse(output.is_building)

        # Mark the build order as completed
        build.complete_build(self.user)
        self.assertEqual(build.status, BuildStatus.COMPLETE)

        # Receive the rest of the line item
        po.receive_line_item(po_line, location, 5, self.user)
        po_line.refresh_from_db()
        self.assertEqual(po_line.received, 10)

        build.refresh_from_db()
        self.assertEqual(build.completed, 10)
        self.assertEqual(build.build_outputs.count(), 2)

        # As the build was already completed, output has been marked as "complete" too
        output = build.build_outputs.order_by('-pk').first()
        self.assertFalse(output.is_building)

    def test_api_filter(self):
        """Test that the 'external' API filter works as expected."""
        self.assignRole('build.view')

        # Create a purchaseable assembly part
        assembly = Part.objects.create(
            name='Test assembly',
            description='A test assembly',
            purchaseable=True,
            assembly=True,
            active=True,
        )

        # Create some build orders
        for i in range(5):
            Build.objects.create(
                part=assembly,
                title=f'Test build order {i}',
                quantity=10,
                external=i % 2 == 0,
            )

        url = reverse('api-build-list')

        response = self.get(url)

        self.assertEqual(len(response.data), 5)

        # Filter by 'external'
        response = self.get(url, {'external': 'true'})
        self.assertEqual(len(response.data), 3)

        # Filter by 'not external'
        response = self.get(url, {'external': 'false'})
        self.assertEqual(len(response.data), 2)


class BuildTaskTests(BuildTestBase):
    """Direct unit tests for the background task functions in build/tasks.py.

    These tests call task functions directly (synchronously) to verify the
    business logic they encapsulate, independently of the API and offload mechanism.
    """

    def setUp(self):
        """Create a stock location available to all task tests."""
        super().setUp()
        self.location = StockLocation.objects.create(name='Task Test Location')

    def allocate_stock(self, output, allocations):
        """Create BuildItem allocations against self.build for the given output."""
        items_to_create = []
        for item, quantity in allocations.items():
            line = BuildLine.objects.filter(
                build=self.build, bom_item__sub_part=item.part
            ).first()
            items_to_create.append(
                BuildItem(
                    build_line=line,
                    stock_item=item,
                    quantity=quantity,
                    install_into=output,
                )
            )
        BuildItem.objects.bulk_create(items_to_create)

    def _setup_complete_build(self):
        """Helper: allocate stock fully and complete all outputs so the build is ready to complete."""
        self.stock_1_1.quantity = 1000
        self.stock_1_1.save()
        self.stock_2_1.quantity = 30
        self.stock_2_1.save()

        self.build.issue_build()

        # Allocate untracked parts
        self.allocate_stock(
            None, {self.stock_1_1: 50, self.stock_1_2: 10, self.stock_2_1: 30}
        )
        # Allocate tracked parts to each output
        self.allocate_stock(self.output_1, {self.stock_3_1: 6})
        self.allocate_stock(self.output_2, {self.stock_3_1: 14})

        self.build.complete_build_output(self.output_1, None)
        self.build.complete_build_output(self.output_2, None)

    # -----------------------------------------------------------------------
    # complete_build_outputs / scrap_build_outputs tasks
    # -----------------------------------------------------------------------

    def test_complete_outputs_task_is_idempotent(self):
        """Duplicate execution of the output completion task must not double-count.

        Regression test: the task never re-checked 'is_building', so a duplicated
        (or redelivered) task run completed the same outputs twice - inflating the
        'completed' count for the build order and duplicating stock history.
        """
        self.build.issue_build()

        outputs = [{'output_id': self.output_1.pk}, {'output_id': self.output_2.pk}]

        build.tasks.complete_build_outputs(
            self.build.pk,
            outputs,
            self.location.pk,
            StockStatus.OK.value,
            user_id=self.user.pk,
        )

        self.build.refresh_from_db()
        self.output_1.refresh_from_db()

        self.assertEqual(self.build.completed, 10)
        self.assertFalse(self.output_1.is_building)

        n_tracking = StockItemTracking.objects.count()

        # Run the task again (simulating a duplicated / redelivered task)
        build.tasks.complete_build_outputs(
            self.build.pk,
            outputs,
            self.location.pk,
            StockStatus.OK.value,
            user_id=self.user.pk,
        )

        # The 'completed' count has not been double-counted,
        # and no additional stock history has been generated
        self.build.refresh_from_db()
        self.assertEqual(self.build.completed, 10)
        self.assertEqual(StockItemTracking.objects.count(), n_tracking)

    def test_complete_output_twice_rejected(self):
        """Completing or scrapping an already-completed output must be rejected.

        Regression test: neither complete_build_output() nor scrap_build_output()
        re-checked the 'is_building' state of the output.
        """
        self.build.issue_build()

        self.build.complete_build_output(self.output_1, None)

        with self.assertRaises(ValidationError):
            self.build.complete_build_output(self.output_1, None)

        with self.assertRaises(ValidationError):
            self.build.scrap_build_output(self.output_1, None, self.location)

        # An output belonging to a *different* build order is also rejected
        with self.assertRaises(ValidationError):
            self.build.complete_build_output(self.stockitem_wo_required_test, None)

    # -----------------------------------------------------------------------
    # cancel_build task
    # -----------------------------------------------------------------------

    def test_cancel_task_discards_allocations(self):
        """cancel_build with remove_allocated_stock=False: allocations deleted, stock not consumed."""
        self.build.issue_build()
        self.allocate_stock(None, {self.stock_1_2: 50})
        self.assertGreater(self.build.allocated_stock.count(), 0)

        build.tasks.cancel_build(
            self.build.pk, self.user.pk, remove_allocated_stock=False
        )

        # BuildItem rows gone
        self.assertEqual(self.build.allocated_stock.count(), 0)
        # Stock item was NOT consumed
        self.assertIsNone(StockItem.objects.get(pk=self.stock_1_2.pk).consumed_by)

    def test_cancel_task_consumes_allocations(self):
        """cancel_build with remove_allocated_stock=True: stock items are marked consumed."""
        self.build.issue_build()
        self.allocate_stock(None, {self.stock_1_2: 50})

        build.tasks.cancel_build(
            self.build.pk, self.user.pk, remove_allocated_stock=True
        )

        # All BuildItem rows gone
        self.assertEqual(self.build.allocated_stock.count(), 0)
        # The allocated (non-trackable) stock was consumed
        self.assertGreater(self.build.consumed_stock.count(), 0)

    def test_cancel_task_removes_incomplete_outputs(self):
        """cancel_build with remove_incomplete_outputs=True: in-progress outputs are deleted."""
        self.build.issue_build()
        initial_count = self.build.build_outputs.filter(is_building=True).count()
        self.assertGreater(initial_count, 0)

        build.tasks.cancel_build(
            self.build.pk, self.user.pk, remove_incomplete_outputs=True
        )

        self.assertEqual(self.build.build_outputs.filter(is_building=True).count(), 0)

    def test_cancel_task_preserves_incomplete_outputs(self):
        """cancel_build with remove_incomplete_outputs=False: in-progress outputs are kept."""
        self.build.issue_build()
        initial_count = self.build.build_outputs.filter(is_building=True).count()
        self.assertGreater(initial_count, 0)

        build.tasks.cancel_build(
            self.build.pk, self.user.pk, remove_incomplete_outputs=False
        )

        self.assertEqual(
            self.build.build_outputs.filter(is_building=True).count(), initial_count
        )

    # -----------------------------------------------------------------------
    # complete_build task
    # -----------------------------------------------------------------------

    @override_settings(
        TESTING_TABLE_EVENTS=True,
        PLUGIN_TESTING_EVENTS=True,
        PLUGIN_TESTING_EVENTS_ASYNC=True,
    )
    def test_complete_build_task_triggers_event(self):
        """complete_build task fires the BuildEvents.COMPLETED event."""
        from django_q.models import OrmQ

        from build.events import BuildEvents

        set_global_setting('ENABLE_PLUGINS_EVENTS', True)
        OrmQ.objects.all().delete()

        self._setup_complete_build()
        self.build.complete_build(self.user)

        task = findOffloadedEvent(BuildEvents.COMPLETED, matching_kwargs=['id'])
        self.assertIsNotNone(task)
        self.assertEqual(task.kwargs()['id'], self.build.pk)

        set_global_setting('ENABLE_PLUGINS_EVENTS', False)

    def test_complete_build_task_trim_stock(self):
        """complete_build with trim_allocated_stock=True removes over-allocations before consuming."""
        self.stock_1_2.quantity = 100
        self.stock_1_2.save()
        self.stock_2_1.quantity = 30
        self.stock_2_1.save()

        self.build.issue_build()

        # Over-allocate sub_part_1: need 50, allocate 100
        self.allocate_stock(None, {self.stock_1_2: 100, self.stock_2_1: 30})
        self.allocate_stock(self.output_1, {self.stock_3_1: 6})
        self.allocate_stock(self.output_2, {self.stock_3_1: 14})

        self.assertTrue(self.build.is_overallocated())

        self.build.complete_build_output(self.output_1, None)
        self.build.complete_build_output(self.output_2, None)
        self.assertTrue(self.build.can_complete)

        self.build.complete_build(self.user, trim_allocated_stock=True)
        self.build.refresh_from_db()
        self.assertEqual(self.build.status, BuildStatus.COMPLETE)

        # Only 50 units of sub_part_1 should have been consumed (not 100)
        consumed_qty = StockItem.objects.filter(
            consumed_by=self.build, part=self.sub_part_1
        ).aggregate(total=Sum('quantity'))['total']
        self.assertEqual(consumed_qty, 50)

    # -----------------------------------------------------------------------
    # delete_build_outputs task
    # -----------------------------------------------------------------------

    def test_delete_build_outputs_skips_missing_id(self):
        """delete_build_outputs silently skips nonexistent output IDs and deletes valid ones."""
        from build.tasks import delete_build_outputs

        # Create an output directly to avoid serial-number requirements on the trackable assembly
        output = StockItem.objects.create(
            part=self.assembly, quantity=3, is_building=True, build=self.build
        )
        real_id = output.pk

        # Mix a valid ID with a nonexistent one — must not raise
        delete_build_outputs(self.build.pk, [real_id, 99999])

        self.assertFalse(StockItem.objects.filter(pk=real_id).exists())

    # -----------------------------------------------------------------------
    # scrap_build_outputs task
    # -----------------------------------------------------------------------

    def test_scrap_build_outputs_discard_allocations(self):
        """scrap_build_outputs with discard_allocations=True removes allocations without consuming stock."""
        from build.tasks import scrap_build_outputs

        self.build.issue_build()
        # Allocate tracked stock to output_1
        self.allocate_stock(self.output_1, {self.stock_3_1: 6})
        self.assertGreater(self.output_1.items_to_install.count(), 0)

        scrap_build_outputs(
            self.build.pk,
            [{'output_id': self.output_1.pk, 'quantity': self.output_1.quantity}],
            location_id=self.location.pk,
            notes='discard test',
            discard_allocations=True,
            user_id=None,
        )

        self.output_1.refresh_from_db()
        self.assertEqual(self.output_1.status, StockStatus.REJECTED.value)
        self.assertFalse(self.output_1.is_building)

        # Allocation rows should be gone
        self.assertEqual(self.output_1.items_to_install.count(), 0)
        # Stock was discarded (not consumed or installed)
        self.stock_3_1.refresh_from_db()
        self.assertIsNone(self.stock_3_1.consumed_by)
        self.assertIsNone(self.stock_3_1.belongs_to)

    def test_scrap_build_outputs_consume_allocations(self):
        """scrap_build_outputs with discard_allocations=False (default) consumes/installs stock."""
        from build.tasks import scrap_build_outputs

        self.build.issue_build()
        self.allocate_stock(self.output_1, {self.stock_3_1: 6})

        scrap_build_outputs(
            self.build.pk,
            [{'output_id': self.output_1.pk, 'quantity': self.output_1.quantity}],
            location_id=self.location.pk,
            notes='consume test',
            discard_allocations=False,
            user_id=None,
        )

        self.output_1.refresh_from_db()
        self.assertEqual(self.output_1.status, StockStatus.REJECTED.value)
        self.assertFalse(self.output_1.is_building)

        # complete_allocation splits stock_3_1 and installs the split piece into output_1
        # (stock_3_1 quantity=1000, only 6 allocated, so a child item is created)
        self.assertTrue(
            StockItem.objects.filter(belongs_to=self.output_1).exists(),
            'Expected a tracked stock item to be installed into the output',
        )

    # -----------------------------------------------------------------------
    # complete_build_outputs task
    # -----------------------------------------------------------------------

    def test_complete_build_outputs_with_status_none(self):
        """complete_build_outputs with status=None falls back to StockStatus.OK in the model."""
        from build.tasks import complete_build_outputs

        self.build.issue_build()
        # Create output directly to avoid serial-number requirements on the trackable assembly
        output = StockItem.objects.create(
            part=self.assembly, quantity=5, is_building=True, build=self.build
        )

        complete_build_outputs(
            self.build.pk,
            [{'output_id': output.pk}],
            location_id=self.location.pk,
            status=None,
            notes='status none test',
            user_id=None,
        )

        output.refresh_from_db()
        self.assertFalse(output.is_building)
        # status=None should resolve to StockStatus.OK (the model default)
        self.assertEqual(output.status, StockStatus.OK.value)
