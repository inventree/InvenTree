"""Unit tests for the 'build' models"""
import uuid
from datetime import datetime, timedelta

from django.test import TestCase

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.models import Sum

from InvenTree import status_codes as status

import common.models
import build.tasks
from build.models import Build, BuildItem, BuildLine, generate_next_build_reference
from part.models import Part, BomItem, BomItemSubstitute, PartTestTemplate
from stock.models import StockItem, StockItemTestResult
from users.models import Owner

import logging
logger = logging.getLogger('inventree')


class BuildTestBase(TestCase):
    """Run some tests to ensure that the Build model is working properly."""

    fixtures = [
        'users',
    ]

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
            name="An assembled part",
            description="Why does it matter what my description is?",
            assembly=True,
            trackable=True,
        )

        # create one build with one required test template
        cls.tested_part_with_required_test = Part.objects.create(
            name="Part having required tests",
            description="Why does it matter what my description is?",
            assembly=True,
            trackable=True,
        )

        cls.test_template_required = PartTestTemplate.objects.create(
            part=cls.tested_part_with_required_test,
            test_name="Required test",
            description="Required test template description",
            required=True,
            requires_value=False,
            requires_attachment=False
        )

        ref = generate_next_build_reference()

        cls.build_w_tests_trackable = Build.objects.create(
            reference=ref,
            title="This is a build",
            part=cls.tested_part_with_required_test,
            quantity=1,
            issued_by=get_user_model().objects.get(pk=1),
        )

        cls.stockitem_with_required_test = StockItem.objects.create(
            part=cls.tested_part_with_required_test,
            quantity=1,
            is_building=True,
            serial=uuid.uuid4(),
            build=cls.build_w_tests_trackable
        )

        # now create a part with a non-required test template
        cls.tested_part_wo_required_test = Part.objects.create(
            name="Part with one non.required test",
            description="Why does it matter what my description is?",
            assembly=True,
            trackable=True,
        )

        cls.test_template_non_required = PartTestTemplate.objects.create(
            part=cls.tested_part_wo_required_test,
            test_name="Required test template",
            description="Required test template description",
            required=False,
            requires_value=False,
            requires_attachment=False
        )

        ref = generate_next_build_reference()

        cls.build_wo_tests_trackable = Build.objects.create(
            reference=ref,
            title="This is a build",
            part=cls.tested_part_wo_required_test,
            quantity=1,
            issued_by=get_user_model().objects.get(pk=1),
        )

        cls.stockitem_wo_required_test = StockItem.objects.create(
            part=cls.tested_part_wo_required_test,
            quantity=1,
            is_building=True,
            serial=uuid.uuid4(),
            build=cls.build_wo_tests_trackable
        )

        cls.sub_part_1 = Part.objects.create(
            name="Widget A",
            description="A widget",
            component=True
        )

        cls.sub_part_2 = Part.objects.create(
            name="Widget B",
            description="A widget",
            component=True
        )

        cls.sub_part_3 = Part.objects.create(
            name="Widget C",
            description="A widget",
            component=True,
            trackable=True
        )

        # Create BOM item links for the parts
        cls.bom_item_1 = BomItem.objects.create(
            part=cls.assembly,
            sub_part=cls.sub_part_1,
            quantity=5
        )

        cls.bom_item_2 = BomItem.objects.create(
            part=cls.assembly,
            sub_part=cls.sub_part_2,
            quantity=3,
            optional=True
        )

        # sub_part_3 is trackable!
        cls.bom_item_3 = BomItem.objects.create(
            part=cls.assembly,
            sub_part=cls.sub_part_3,
            quantity=2
        )

        ref = generate_next_build_reference()

        # Create a "Build" object to make 10x objects
        cls.build = Build.objects.create(
            reference=ref,
            title="This is a build",
            part=cls.assembly,
            quantity=10,
            issued_by=get_user_model().objects.get(pk=1),
        )

        # Create some BuildLine items we can use later on
        cls.line_1 = BuildLine.objects.get(build=cls.build, bom_item=cls.bom_item_1)
        cls.line_2 = BuildLine.objects.get(build=cls.build, bom_item=cls.bom_item_2)
        cls.line_3 = BuildLine.objects.get(build=cls.build, bom_item=cls.bom_item_3)

        # Create some build output (StockItem) objects
        cls.output_1 = StockItem.objects.create(
            part=cls.assembly,
            quantity=3,
            is_building=True,
            build=cls.build
        )

        cls.output_2 = StockItem.objects.create(
            part=cls.assembly,
            quantity=7,
            is_building=True,
            build=cls.build,
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
    """Unit testing class for the Build model"""

    def test_ref_int(self):
        """Test the "integer reference" field used for natural sorting"""
        # Set build reference to new value
        common.models.InvenTreeSetting.set_setting('BUILDORDER_REFERENCE_PATTERN', 'BO-{ref}-???', change_user=None)

        refs = {
            'BO-123-456': 123,
            'BO-456-123': 456,
            'BO-999-ABC': 999,
            'BO-123ABC-ABC': 123,
            'BO-ABC123-ABC': 123,
        }

        for ref, ref_int in refs.items():
            build = Build(
                reference=ref,
                quantity=1,
                part=self.assembly,
                title='Making some parts',
            )

            self.assertEqual(build.reference_int, 0)
            build.save()
            self.assertEqual(build.reference_int, ref_int)

        # Set build reference back to default value
        common.models.InvenTreeSetting.set_setting('BUILDORDER_REFERENCE_PATTERN', 'BO-{ref:04d}', change_user=None)

    def test_ref_validation(self):
        """Test that the reference field validation works as expected"""
        # Default reference pattern = 'BO-{ref:04d}
        # These patterns should fail
        for ref in [
            'BO-1234x',
            'BO1234',
            'OB-1234',
            'BO--1234'
        ]:
            with self.assertRaises(ValidationError):
                Build.objects.create(
                    part=self.assembly,
                    quantity=10,
                    reference=ref,
                    title='Invalid reference',
                )

        for ref in [
            'BO-1234',
            'BO-9999',
            'BO-123'
        ]:
            Build.objects.create(
                part=self.assembly,
                quantity=10,
                reference=ref,
                title='Valid reference',
            )

        # Try a new validator pattern
        common.models.InvenTreeSetting.set_setting('BUILDORDER_REFERENCE_PATTERN', '{ref}-BO', change_user=None)

        for ref in [
            '1234-BO',
            '9999-BO'
        ]:
            Build.objects.create(
                part=self.assembly,
                quantity=10,
                reference=ref,
                title='Valid reference',
            )

        # Set build reference back to default value
        common.models.InvenTreeSetting.set_setting('BUILDORDER_REFERENCE_PATTERN', 'BO-{ref:04d}', change_user=None)

    def test_next_ref(self):
        """Test that the next reference is automatically generated"""
        common.models.InvenTreeSetting.set_setting('BUILDORDER_REFERENCE_PATTERN', 'XYZ-{ref:06d}', change_user=None)

        build = Build.objects.create(
            part=self.assembly,
            quantity=5,
            reference='XYZ-987',
            title='Some thing',
        )

        self.assertEqual(build.reference_int, 987)

        # Now create one *without* specifying the reference
        build = Build.objects.create(
            part=self.assembly,
            quantity=1,
            title='Some new title',
        )

        self.assertEqual(build.reference, 'XYZ-000988')
        self.assertEqual(build.reference_int, 988)

        # Set build reference back to default value
        common.models.InvenTreeSetting.set_setting('BUILDORDER_REFERENCE_PATTERN', 'BO-{ref:04d}', change_user=None)

    def test_init(self):
        """Perform some basic tests before we start the ball rolling"""
        self.assertEqual(StockItem.objects.count(), 12)

        # Build is PENDING
        self.assertEqual(self.build.status, status.BuildStatus.PENDING)

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
        """Ensure that dodgy BuildItem objects cannot be created"""
        stock = StockItem.objects.create(part=self.assembly, quantity=99)

        # Create a BuiltItem which points to an invalid StockItem
        b = BuildItem(stock_item=stock, build_line=self.line_2, quantity=10)

        with self.assertRaises(ValidationError):
            b.save()

        # Create a BuildItem which has too much stock assigned
        b = BuildItem(stock_item=self.stock_1_1, build_line=self.line_1, quantity=9999999)

        with self.assertRaises(ValidationError):
            b.clean()

        # Negative stock? Not on my watch!
        b = BuildItem(stock_item=self.stock_1_1, build_line=self.line_1, quantity=-99)

        with self.assertRaises(ValidationError):
            b.clean()

        # Ok, what about we make one that does *not* fail?
        b = BuildItem(stock_item=self.stock_1_2, build_line=self.line_1, install_into=self.output_1, quantity=10)
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
        items_to_create = []

        for item, quantity in allocations.items():

            # Find an appropriate BuildLine to allocate against
            line = BuildLine.objects.filter(
                build=self.build,
                bom_item__sub_part=item.part
            ).first()

            items_to_create.append(BuildItem(
                build_line=line,
                stock_item=item,
                quantity=quantity,
                install_into=output
            ))

        BuildItem.objects.bulk_create(items_to_create)

    def test_partial_allocation(self):
        """Test partial allocation of stock"""
        # Fully allocate tracked stock against build output 1
        self.allocate_stock(
            self.output_1,
            {
                self.stock_3_1: 6,
            }
        )

        self.assertTrue(self.build.is_output_fully_allocated(self.output_1))

        # Partially allocate tracked stock against build output 2
        self.allocate_stock(
            self.output_2,
            {
                self.stock_3_1: 1,
            }
        )

        self.assertFalse(self.build.is_output_fully_allocated(self.output_2))

        # Partially allocate untracked stock against build
        self.allocate_stock(
            None,
            {
                self.stock_1_1: 1,
                self.stock_2_1: 1
            }
        )

        self.assertFalse(self.build.is_output_fully_allocated(None))

        # Find lines which are *not* fully allocated
        unallocated = self.build.unallocated_lines()

        self.assertEqual(len(unallocated), 3)

        self.allocate_stock(
            None,
            {
                self.stock_1_2: 100,
            }
        )

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
        self.allocate_stock(
            None,
            {
                self.stock_1_2: 50,
                self.stock_2_1: 50,
            }
        )

        self.assertTrue(self.build.is_fully_allocated(tracked=False))

    def test_overallocation_and_trim(self):
        """Test overallocation of stock and trim function"""
        # Fully allocate tracked stock (not eligible for trimming)
        self.allocate_stock(
            self.output_1,
            {
                self.stock_3_1: 6,
            }
        )
        self.allocate_stock(
            self.output_2,
            {
                self.stock_3_1: 14,
            }
        )
        # Fully allocate part 1 (should be left alone)
        self.allocate_stock(
            None,
            {
                self.stock_1_1: 3,
                self.stock_1_2: 47,
            }
        )

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
                extra_2_1: 6,       # 31
                extra_2_2: 4,       # 35
            }
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
        self.assertEqual(items.filter(consumed_by=None).aggregate(Sum('quantity'))['quantity__sum'], 5)

        # And the "consumed_by" quantity has been increased
        self.assertEqual(items.filter(consumed_by=self.build).aggregate(Sum('quantity'))['quantity__sum'], 30)

        self.assertEqual(StockItem.objects.get(pk=self.stock_3_1.pk).quantity, 980)

        # Check that the "consumed_by" item count has increased
        self.assertEqual(StockItem.objects.filter(consumed_by=self.build).count(), n + 8)

    def test_change_part(self):
        """Try to change target part after creating a build"""

        bo = Build.objects.create(
            reference='BO-9999',
            title='Some new build',
            part=self.assembly,
            quantity=5,
            issued_by=get_user_model().objects.get(pk=1),
        )

        assembly_2 = Part.objects.create(
            name="Another assembly",
            description="A different assembly",
            assembly=True,
        )

        # Should not be able to change the part after the Build is saved
        with self.assertRaises(ValidationError):
            bo.part = assembly_2
            bo.clean()

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

    def test_complete_with_required_tests(self):
        """Test the prevention completion when a required test is missing feature"""

        # with required tests incompleted the save should fail
        common.models.InvenTreeSetting.set_setting('PREVENT_BUILD_COMPLETION_HAVING_INCOMPLETED_TESTS', True, change_user=None)

        with self.assertRaises(ValidationError):
            self.build_w_tests_trackable.complete_build_output(self.stockitem_with_required_test, None)

        # let's complete the required test and see if it could be saved
        StockItemTestResult.objects.create(
            stock_item=self.stockitem_with_required_test,
            test=self.test_template_required.test_name,
            result=True
        )
        self.build_w_tests_trackable.complete_build_output(self.stockitem_with_required_test, None)

        # let's see if a non required test could be saved
        self.build_wo_tests_trackable.complete_build_output(self.stockitem_wo_required_test, None)

    def test_overdue_notification(self):
        """Test sending of notifications when a build order is overdue."""
        self.build.target_date = datetime.now().date() - timedelta(days=1)
        self.build.save()

        # Check for overdue orders
        build.tasks.check_overdue_build_orders()

        message = common.models.NotificationMessage.objects.get(
            category='build.overdue_build_order',
            user__id=1,
        )

        self.assertEqual(message.name, 'Overdue Build Order')

    def test_new_build_notification(self):
        """Test that a notification is sent when a new build is created"""
        Build.objects.create(
            reference='BO-9999',
            title='Some new build',
            part=self.assembly,
            quantity=5,
            issued_by=get_user_model().objects.get(pk=2),
            responsible=Owner.create(obj=Group.objects.get(pk=3))
        )

        # Two notifications should have been sent
        messages = common.models.NotificationMessage.objects.filter(
            category='build.new_build',
        )

        self.assertEqual(messages.count(), 1)

        self.assertFalse(messages.filter(user__pk=2).exists())

        # Inactive users do not receive notifications
        self.assertFalse(messages.filter(user__pk=3).exists())

        self.assertTrue(messages.filter(user__pk=4).exists())

    def test_metadata(self):
        """Unit tests for the metadata field."""
        # Make sure a BuildItem exists before trying to run this test
        b = BuildItem(stock_item=self.stock_1_2, build_line=self.line_1, install_into=self.output_1, quantity=10)
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

        self.assertFalse(self.build.is_fully_allocated(tracked=False))

        # Stock is not interchangeable, nothing will happen
        self.build.auto_allocate_stock(
            interchangeable=False,
            substitutes=False,
        )

        self.assertFalse(self.build.is_fully_allocated(tracked=False))

        self.assertEqual(self.build.allocated_stock.count(), 0)

        self.assertFalse(self.line_1.is_fully_allocated())
        self.assertFalse(self.line_2.is_fully_allocated())

        self.assertEqual(self.line_1.unallocated_quantity(), 50)
        self.assertEqual(self.line_2.unallocated_quantity(), 30)

        # This time we expect stock to be allocated!
        self.build.auto_allocate_stock(
            interchangeable=True,
            substitutes=False,
            optional_items=True,
        )

        self.assertFalse(self.build.is_fully_allocated(tracked=False))

        self.assertEqual(self.build.allocated_stock.count(), 7)

        self.assertTrue(self.line_1.is_fully_allocated())
        self.assertFalse(self.line_2.is_fully_allocated())

        self.assertEqual(self.line_1.unallocated_quantity(), 0)
        self.assertEqual(self.line_2.unallocated_quantity(), 5)

        # This time, allow substitute parts to be used!
        self.build.auto_allocate_stock(
            interchangeable=True,
            substitutes=True,
        )

        self.assertEqual(self.line_1.unallocated_quantity(), 0)
        self.assertEqual(self.line_2.unallocated_quantity(), 5)

        self.assertTrue(self.line_1.is_fully_allocated())
        self.assertFalse(self.line_2.is_fully_allocated())

    def test_fully_auto(self):
        """We should be able to auto-allocate against a build in a single go"""
        self.build.auto_allocate_stock(
            interchangeable=True,
            substitutes=True,
            optional_items=True,
        )

        self.assertTrue(self.build.is_fully_allocated(tracked=False))

        self.assertEqual(self.line_1.unallocated_quantity(), 0)
        self.assertEqual(self.line_2.unallocated_quantity(), 0)
