"""Basic unit tests for the BuildOrder app."""

from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.urls import reverse

from build.status_codes import BuildStatus, RepairOrderStatus
from common.settings import set_global_setting
from InvenTree.unit_test import AdminTestCase, InvenTreeAPITestCase, InvenTreeTestCase
from part.models import BomItem, Part

from .models import Build, RepairOrder


class BuildTestSimple(InvenTreeTestCase):
    """Basic set of tests for the BuildOrder model functionality."""

    fixtures = ['category', 'part', 'location', 'build', 'stock']

    roles = ['build.change', 'build.add', 'build.delete']

    def test_build_objects(self):
        """Ensure the Build objects were correctly created."""
        self.assertEqual(Build.objects.count(), 5)
        b = Build.objects.get(pk=2)
        self.assertEqual(b.batch, 'B2')
        self.assertEqual(b.quantity, 21)

        self.assertEqual(str(b), 'BO-0002')

    def test_url(self):
        """Test URL lookup."""
        b1 = Build.objects.get(pk=1)
        self.assertEqual(b1.get_absolute_url(), '/web/manufacturing/build-order/1')

    def test_is_complete(self):
        """Test build completion status."""
        b1 = Build.objects.get(pk=1)
        b2 = Build.objects.get(pk=2)

        self.assertEqual(b1.is_complete, False)
        self.assertEqual(b2.is_complete, True)

        self.assertEqual(b2.status, BuildStatus.COMPLETE)

    def test_overdue(self):
        """Test overdue status functionality."""
        today = datetime.now().date()

        build = Build.objects.get(pk=1)
        self.assertFalse(build.is_overdue)

        build.target_date = today - timedelta(days=1)
        build.save()
        self.assertTrue(build.is_overdue)

        build.target_date = today + timedelta(days=80)
        build.save()
        self.assertFalse(build.is_overdue)

    def test_is_active(self):
        """Test active / inactive build status."""
        b1 = Build.objects.get(pk=1)
        b2 = Build.objects.get(pk=2)

        self.assertEqual(b1.is_active, True)
        self.assertEqual(b2.is_active, False)

    def test_cancel_build(self):
        """Test build cancellation function."""
        build = Build.objects.get(id=1)

        self.assertEqual(build.status, BuildStatus.PENDING)

        build.cancel_build(self.user)

        self.assertEqual(build.status, BuildStatus.CANCELLED)

    def test_build_create(self):
        """Test creation of build orders via API."""
        n = Build.objects.count()

        # Find an assembly part
        assembly = Part.objects.filter(assembly=True).first()

        assembly.active = True
        assembly.locked = False
        assembly.save()

        self.assertEqual(assembly.get_bom_items().count(), 0)

        # Let's create some BOM items for this assembly
        for component in Part.objects.filter(assembly=False, component=True)[:15]:
            try:
                BomItem.objects.create(
                    part=assembly, sub_part=component, reference='xxx', quantity=5
                )
            except ValidationError:
                pass

        # The assembly has a BOM, and is now *invalid*
        self.assertGreater(assembly.get_bom_items().count(), 0)
        self.assertFalse(assembly.is_bom_valid())

        # Create a build for an assembly with an *invalid* BOM
        set_global_setting('BUILDORDER_REQUIRE_VALID_BOM', False)
        set_global_setting('BUILDORDER_REQUIRE_ACTIVE_PART', True)
        set_global_setting('BUILDORDER_REQUIRE_LOCKED_PART', False)

        bo = Build.objects.create(part=assembly, quantity=10, reference='BO-9990')
        bo.save()

        # Now, require a *valid* BOM
        set_global_setting('BUILDORDER_REQUIRE_VALID_BOM', True)

        with self.assertRaises(ValidationError):
            bo = Build.objects.create(part=assembly, quantity=10, reference='BO-9991')

        # Now, validate the BOM, and try again
        assembly.validate_bom(None)
        self.assertTrue(assembly.is_bom_valid())

        bo = Build.objects.create(part=assembly, quantity=10, reference='BO-9992')

        # Now, try and create a build for an inactive assembly
        assembly.active = False
        assembly.save()

        with self.assertRaises(ValidationError):
            bo = Build.objects.create(part=assembly, quantity=10, reference='BO-9993')

        set_global_setting('BUILDORDER_REQUIRE_ACTIVE_PART', False)
        Build.objects.create(part=assembly, quantity=10, reference='BO-9994')

        # Check that the "locked" requirement works
        set_global_setting('BUILDORDER_REQUIRE_LOCKED_PART', True)
        with self.assertRaises(ValidationError):
            Build.objects.create(part=assembly, quantity=10, reference='BO-9995')

        assembly.locked = True
        assembly.save()

        Build.objects.create(part=assembly, quantity=10, reference='BO-9996')

        # Check that expected quantity of new builds is created
        self.assertEqual(Build.objects.count(), n + 4)


class BuildTreeTest(InvenTreeTestCase):
    """Unit tests for the Build tree structure."""

    @classmethod
    def setUpTestData(cls):
        """Initialize test data for the Build tree tests."""
        from build.models import Build
        from part.models import Part

        # Create a test assembly part
        cls.assembly = Part.objects.create(
            name='Test Assembly',
            description='A test assembly part',
            assembly=True,
            active=True,
            locked=False,
        )

        # Generate a top-level build
        cls.build = Build.objects.create(
            part=cls.assembly, quantity=5, reference='BO-1234', target_date=None
        )

    def test_basic_tree(self):
        """Test basic tree structure functionality.

        - In this test we test a simple non-branching tree structure.
        - Check that the tree structure is correctly created.
        - Verify parent-child relationships and tree properties.
        - Ensure that the number of children and descendants is as expected.
        - Validate that the tree properties (tree_id, level, lft, rght) are correct
        - Check that node deletion works correctly.
        """
        from build.models import Build

        # Create a cascading tree structure of builds
        child = self.build

        builds = [self.build]

        self.assertEqual(Build.objects.count(), 1)

        for i in range(10):
            child = Build.objects.create(
                part=self.assembly, quantity=2, reference=f'BO-{1235 + i}', parent=child
            )

            builds.append(child)

        self.assertEqual(Build.objects.count(), 11)

        # Test the tree structure for each node
        for idx, child in enumerate(builds):
            child.refresh_from_db()

            # Check parent-child relationships
            expected_parent = builds[idx - 1] if idx > 0 else None
            self.assertEqual(child.parent, expected_parent)

            # Check number of children
            expected_children = 0 if idx == 10 else 1
            self.assertEqual(child.get_children().count(), expected_children)

            # Check number of descendants
            expected_descendants = max(10 - idx, 0)
            self.assertEqual(
                child.get_descendants(include_self=False).count(), expected_descendants
            )

            # Test tree structure
            self.assertEqual(child.tree_id, self.build.tree_id)
            self.assertEqual(child.level, idx)
            self.assertEqual(child.lft, idx + 1)
            self.assertEqual(child.rght, 22 - idx)

        # Test deletion of a node - delete BO-1238
        Build.objects.get(reference='BO-1238').delete()

        # We expect that only a SINGLE node is deleted
        self.assertEqual(Build.objects.count(), 10)
        self.assertEqual(self.build.get_descendants(include_self=False).count(), 9)

        # Check that the item parents have been correctly remapped
        build_reference_map = {
            'BO-1235': 'BO-1234',
            'BO-1236': 'BO-1235',
            'BO-1237': 'BO-1236',
            'BO-1239': 'BO-1237',  # BO-1238 was deleted, so BO-1239's parent is now BO-1237
            'BO-1240': 'BO-1239',
            'BO-1241': 'BO-1240',
            'BO-1242': 'BO-1241',
            'BO-1243': 'BO-1242',
            'BO-1244': 'BO-1243',
        }

        # Check that the tree structure is still valid
        for child_ref, parent_ref in build_reference_map.items():
            build = Build.objects.get(reference=child_ref)
            parent = Build.objects.get(reference=parent_ref)
            self.assertEqual(parent_ref, parent.reference)
            self.assertEqual(build.tree_id, self.build.tree_id)
            self.assertEqual(build.level, parent.level + 1)
            self.assertEqual(build.lft, parent.lft + 1)
            self.assertEqual(build.rght, parent.rght - 1)

    def test_complex_tree(self):
        """Test a more complex tree structure with multiple branches.

        - Ensure that grafting nodes works correctly.
        """
        ref = 1235

        for ii in range(3):
            # Create child builds
            child = Build.objects.create(
                part=self.assembly,
                quantity=2,
                reference=f'BO-{ref + (ii * 4)}',
                parent=self.build,
            )

            for jj in range(3):
                # Create grandchild builds
                grandchild = Build.objects.create(
                    part=self.assembly,
                    quantity=2,
                    reference=f'BO-{ref + (ii * 4) + jj + 1}',
                    parent=child,
                )

                self.assertEqual(grandchild.parent, child)
                self.assertEqual(grandchild.tree_id, self.build.tree_id)
                self.assertEqual(grandchild.level, 2)

            child.refresh_from_db()

            self.assertEqual(child.get_children().count(), 3)
            self.assertEqual(child.get_descendants(include_self=False).count(), 3)

            self.assertEqual(child.level, 1)
            self.assertEqual(child.tree_id, self.build.tree_id)

        self.build.refresh_from_db()

        # Basic tests
        self.assertEqual(Build.objects.count(), 13)
        self.assertEqual(self.build.get_children().count(), 3)
        self.assertEqual(self.build.get_descendants(include_self=False).count(), 12)

        # Move one of the child builds
        build = Build.objects.get(reference='BO-1239')
        self.assertEqual(build.parent.reference, 'BO-1234')
        self.assertEqual(build.level, 1)
        self.assertEqual(build.get_children().count(), 3)
        for bo in build.get_children():
            self.assertEqual(bo.level, 2)

        parent = Build.objects.get(reference='BO-1235')
        build.parent = parent
        build.save()

        build = Build.objects.get(reference='BO-1239')
        self.assertEqual(build.parent.reference, 'BO-1235')
        self.assertEqual(build.level, 2)
        self.assertEqual(build.get_children().count(), 3)
        for bo in build.get_children():
            self.assertEqual(bo.level, 3)


class RepairOrderTransitionTests(InvenTreeTestCase):
    """Tests for RepairOrder state machine transitions.

    Exercises the full repair lifecycle to ensure all four
    @inventree_transition-decorated methods work correctly.
    """

    roles = ['build.change', 'build.add', 'build.delete']

    @classmethod
    def setUpTestData(cls):
        """Create an assembly Part for repair orders to be scoped to."""
        super().setUpTestData()

        cls.assembly = Part.objects.create(
            name='Repair Test Assembly',
            description='A test assembly part for repair orders',
            assembly=True,
            active=True,
            locked=False,
        )

    def test_repair_order_lifecycle(self):
        """Walk a RepairOrder through a full lifecycle.

        PENDING → IN_PROGRESS → ON_HOLD → IN_PROGRESS → COMPLETE.
        Exercises issue_repair, hold_repair, and complete_repair.
        """
        ro = RepairOrder.objects.create(
            reference='RO-0001',
            description='Lifecycle test repair order',
            part=self.assembly,
        )
        self.assertEqual(ro.status, RepairOrderStatus.PENDING.value)

        # PENDING → IN_PROGRESS
        ro.issue_repair()
        ro.refresh_from_db()
        self.assertEqual(ro.status, RepairOrderStatus.IN_PROGRESS.value)

        # IN_PROGRESS → ON_HOLD
        ro.hold_repair()
        ro.refresh_from_db()
        self.assertEqual(ro.status, RepairOrderStatus.ON_HOLD.value)

        # ON_HOLD → IN_PROGRESS (resume)
        ro.issue_repair()
        ro.refresh_from_db()
        self.assertEqual(ro.status, RepairOrderStatus.IN_PROGRESS.value)

        # IN_PROGRESS → COMPLETE
        ro.complete_repair()
        ro.refresh_from_db()
        self.assertEqual(ro.status, RepairOrderStatus.COMPLETE.value)

    def test_repair_order_cancel_lifecycle(self):
        """Walk a RepairOrder through a cancellation lifecycle.

        PENDING → IN_PROGRESS → CANCELLED.
        Exercises issue_repair and cancel_repair.
        """
        ro = RepairOrder.objects.create(
            reference='RO-0002',
            description='Cancel lifecycle test repair order',
            part=self.assembly,
        )
        self.assertEqual(ro.status, RepairOrderStatus.PENDING.value)

        # PENDING → IN_PROGRESS
        ro.issue_repair()
        ro.refresh_from_db()
        self.assertEqual(ro.status, RepairOrderStatus.IN_PROGRESS.value)

        # IN_PROGRESS → CANCELLED
        ro.cancel_repair()
        ro.refresh_from_db()
        self.assertEqual(ro.status, RepairOrderStatus.CANCELLED.value)


class RepairOrderAPITests(InvenTreeAPITestCase):
    """API-level tests for RepairOrder endpoints.

    Covers:
    - Permission gating (403 without repair_order role)
    - FSM transition endpoints (issue, hold, complete, cancel)
    - Serializer validation (read-only status field)
    - Line item and allocation validation
    - Stock consumption on completion
    """

    fixtures = ['category', 'part', 'location', 'stock']

    # Start with NO roles — we test permission denial first
    roles = []

    def setUp(self):
        """Create a RepairOrder and a Part for tests to act on."""
        super().setUp()

        # Grant repair_order add/change/delete so most tests pass.
        # Individual tests that check permission denial will remove roles first.
        self.assignRole('repair_order.add')
        self.assignRole('repair_order.change')
        self.assignRole('repair_order.delete')
        self.assignRole('repair_order.view')

        # Needed for 'part_detail' to be included in serialized output -
        # OptionalField gates embedded model data behind view permission
        # on that model (see InvenTree.serializers.check_field_permission).
        self.assignRole('part.view')

        # Pick a Part from the fixture so part-related tests have a target.
        self.part = Part.objects.filter(assembly=True).first()

        self.ro = RepairOrder.objects.create(
            reference='RO-0003', description='API test repair order', part=self.part
        )

    # ── Permission gating ──────────────────────────────────────────

    def test_list_requires_role(self):
        """GET /api/build/repair/ returns 403 without repair_order.view."""
        # Remove all roles
        self.clearRoles()

        url = reverse('api-repair-order-list')
        self.get(url, expected_code=403)

    def test_list_with_role(self):
        """GET /api/build/repair/ returns 200 with repair_order.view."""
        url = reverse('api-repair-order-list')
        response = self.get(url, expected_code=200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_requires_role(self):
        """POST /api/build/repair/ returns 403 without repair_order.add."""
        self.clearRoles()

        url = reverse('api-repair-order-list')
        self.post(url, {'description': 'should fail'}, expected_code=403)

    def test_create_with_role(self):
        """POST /api/build/repair/ creates an order with correct defaults."""
        url = reverse('api-repair-order-list')
        data = self.post(
            url,
            {'description': 'Created via API', 'part': self.part.pk},
            expected_code=201,
        ).data

        self.assertIn('pk', data)
        self.assertEqual(data['status'], RepairOrderStatus.PENDING.value)
        self.assertEqual(data['part'], self.part.pk)

    # ── Serializer validation ──────────────────────────────────────

    def test_status_is_read_only(self):
        """PATCH should not allow direct status changes (read-only field)."""
        url = reverse('api-repair-order-detail', kwargs={'pk': self.ro.pk})
        self.patch(url, {'status': RepairOrderStatus.COMPLETE.value}, expected_code=200)
        self.ro.refresh_from_db()
        # Status must NOT have changed — it's read-only
        self.assertEqual(self.ro.status, RepairOrderStatus.PENDING.value)

    def test_completion_date_is_read_only(self):
        """PATCH should not allow directly setting completion_date - it's set by complete_repair()."""
        url = reverse('api-repair-order-detail', kwargs={'pk': self.ro.pk})
        today = datetime.now().date()
        self.patch(url, {'completion_date': today.isoformat()}, expected_code=200)
        self.ro.refresh_from_db()
        self.assertIsNone(self.ro.completion_date)

    # ── FSM transition endpoints ───────────────────────────────────

    def test_issue_transition(self):
        """POST issue/ moves PENDING → IN_PROGRESS."""
        url = reverse('api-repair-order-issue', kwargs={'pk': self.ro.pk})
        self.post(url, expected_code=201)
        self.ro.refresh_from_db()
        self.assertEqual(self.ro.status, RepairOrderStatus.IN_PROGRESS.value)

    def test_hold_transition(self):
        """POST hold/ moves PENDING → ON_HOLD."""
        url = reverse('api-repair-order-hold', kwargs={'pk': self.ro.pk})
        self.post(url, expected_code=201)
        self.ro.refresh_from_db()
        self.assertEqual(self.ro.status, RepairOrderStatus.ON_HOLD.value)

    def test_complete_transition(self):
        """POST complete/ moves PENDING → COMPLETE."""
        url = reverse('api-repair-order-complete', kwargs={'pk': self.ro.pk})
        self.post(url, expected_code=201)
        self.ro.refresh_from_db()
        self.assertEqual(self.ro.status, RepairOrderStatus.COMPLETE.value)
        self.assertIsNotNone(self.ro.completion_date)

    def test_cancel_transition(self):
        """POST cancel/ moves PENDING → CANCELLED."""
        url = reverse('api-repair-order-cancel', kwargs={'pk': self.ro.pk})
        self.post(url, expected_code=201)
        self.ro.refresh_from_db()
        self.assertEqual(self.ro.status, RepairOrderStatus.CANCELLED.value)

    def test_transition_requires_role(self):
        """POST issue/ returns 403 without repair_order.add."""
        self.clearRoles()

        url = reverse('api-repair-order-issue', kwargs={'pk': self.ro.pk})
        self.post(url, expected_code=403)

    def test_full_fsm_via_api(self):
        """Full lifecycle via API: PENDING → IN_PROGRESS → ON_HOLD → IN_PROGRESS → COMPLETE."""
        pk = self.ro.pk

        # PENDING → IN_PROGRESS
        self.post(
            reverse('api-repair-order-issue', kwargs={'pk': pk}), expected_code=201
        )

        # IN_PROGRESS → ON_HOLD
        self.post(
            reverse('api-repair-order-hold', kwargs={'pk': pk}), expected_code=201
        )

        # ON_HOLD → IN_PROGRESS (resume)
        self.post(
            reverse('api-repair-order-issue', kwargs={'pk': pk}), expected_code=201
        )

        # IN_PROGRESS → COMPLETE
        self.post(
            reverse('api-repair-order-complete', kwargs={'pk': pk}), expected_code=201
        )

        self.ro.refresh_from_db()
        self.assertEqual(self.ro.status, RepairOrderStatus.COMPLETE.value)

    def test_locked_order_rejects_transitions(self):
        """A completed order should reject further transitions."""
        # Complete the order (transition already persists the new status)
        self.ro.complete_repair()

        # Attempt to issue again — should fail
        url = reverse('api-repair-order-issue', kwargs={'pk': self.ro.pk})
        self.post(url, expected_code=400)

    # ── Line item and allocation validation ────────────────────────

    def test_line_item_creation(self):
        """Create a line item via the API."""
        p = Part.objects.filter(component=True).first()

        url = reverse('api-repair-order-line-list')
        data = self.post(
            url, {'order': self.ro.pk, 'part': p.pk, 'quantity': 3}, expected_code=201
        ).data

        self.assertEqual(data['order'], self.ro.pk)
        self.assertEqual(float(data['quantity']), 3.0)

    def test_allocation_creation_and_consumption(self):
        """Allocate stock to a line item, then complete the order.

        Verify that the stock quantity is reduced after completion.
        """
        from stock.models import StockItem

        p = Part.objects.filter(component=True).first()
        if p is None:
            self.skipTest('No component parts available')

        # Find or create a stock item for this part
        si = StockItem.objects.filter(part=p, quantity__gte=5).first()
        if si is None:
            from stock.models import StockLocation

            loc = StockLocation.objects.first()
            si = StockItem.objects.create(part=p, quantity=100, location=loc)

        original_qty = float(si.quantity)

        # Create a line item
        from build.models import RepairOrderLineItem

        line = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=2)

        # Create an allocation
        from build.models import RepairOrderAllocation

        alloc = RepairOrderAllocation.objects.create(line=line, item=si, quantity=2)
        alloc.full_clean()  # Validate — should pass

        # Complete the order (consumes stock; transition already persists the new status)
        self.ro.issue_repair()
        self.ro.complete_repair(user=self.user)

        si.refresh_from_db()
        self.assertEqual(float(si.quantity), original_qty - 2)

        # Allocation should be deleted after completion
        self.assertEqual(
            RepairOrderAllocation.objects.filter(line__order=self.ro).count(), 0
        )

    def test_cancel_releases_allocations(self):
        """Cancelling an order deletes all allocations without consuming stock."""
        from stock.models import StockItem

        p = Part.objects.filter(component=True).first()
        if p is None:
            self.skipTest('No component parts available')

        si = StockItem.objects.filter(part=p, quantity__gte=5).first()
        if si is None:
            from stock.models import StockLocation

            loc = StockLocation.objects.first()
            si = StockItem.objects.create(part=p, quantity=100, location=loc)

        original_qty = float(si.quantity)

        from build.models import RepairOrderAllocation, RepairOrderLineItem

        line = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=3)
        RepairOrderAllocation.objects.create(line=line, item=si, quantity=3)

        # Cancel the order (transition already persists the new status)
        self.ro.cancel_repair()

        si.refresh_from_db()
        # Stock should NOT have been consumed
        self.assertEqual(float(si.quantity), original_qty)

        # Allocations should be deleted
        self.assertEqual(
            RepairOrderAllocation.objects.filter(line__order=self.ro).count(), 0
        )

    # ── Filtering and ordering ──────────────────────────────────────

    def test_outstanding_filter(self):
        """The 'outstanding' filter should only match open repair orders."""
        # self.ro is PENDING (open) by default
        completed = RepairOrder.objects.create(
            reference='RO-1001', description='Completed order', part=self.part
        )
        completed.complete_repair()

        url = reverse('api-repair-order-list')

        response = self.get(url, {'outstanding': True}, expected_code=200)
        pks = {item['pk'] for item in response.data}
        self.assertIn(self.ro.pk, pks)
        self.assertNotIn(completed.pk, pks)

        response = self.get(url, {'outstanding': False}, expected_code=200)
        pks = {item['pk'] for item in response.data}
        self.assertNotIn(self.ro.pk, pks)
        self.assertIn(completed.pk, pks)

    def test_overdue_filter(self):
        """The 'overdue' filter should only match open orders past their target date."""
        today = datetime.now().date()

        overdue = RepairOrder.objects.create(
            reference='RO-1002',
            description='Overdue order',
            target_date=today - timedelta(days=5),
            part=self.part,
        )

        not_overdue = RepairOrder.objects.create(
            reference='RO-1003',
            description='Not overdue order',
            target_date=today + timedelta(days=5),
            part=self.part,
        )

        url = reverse('api-repair-order-list')

        response = self.get(url, {'overdue': True}, expected_code=200)
        pks = {item['pk'] for item in response.data}
        self.assertIn(overdue.pk, pks)
        self.assertNotIn(not_overdue.pk, pks)
        self.assertNotIn(self.ro.pk, pks)  # no target_date set

        response = self.get(url, {'overdue': False}, expected_code=200)
        pks = {item['pk'] for item in response.data}
        self.assertNotIn(overdue.pk, pks)
        self.assertIn(not_overdue.pk, pks)

    def test_reference_filter(self):
        """The 'reference' filter should match exactly (case-insensitive)."""
        url = reverse('api-repair-order-list')

        response = self.get(
            url, {'reference': self.ro.reference.lower()}, expected_code=200
        )
        pks = {item['pk'] for item in response.data}
        self.assertEqual(pks, {self.ro.pk})

    def test_target_date_ordering(self):
        """Repair orders should be sortable by target_date."""
        today = datetime.now().date()

        first = RepairOrder.objects.create(
            reference='RO-1004',
            description='Earlier',
            target_date=today,
            part=self.part,
        )
        second = RepairOrder.objects.create(
            reference='RO-1005',
            description='Later',
            target_date=today + timedelta(days=10),
            part=self.part,
        )

        url = reverse('api-repair-order-list')

        response = self.get(url, {'ordering': 'target_date'}, expected_code=200)
        pks = [item['pk'] for item in response.data]
        self.assertLess(pks.index(first.pk), pks.index(second.pk))

    def test_start_date_target_date_ordering_validated(self):
        """A start_date after the target_date should be rejected."""
        today = datetime.now().date()

        ro = RepairOrder(
            reference='RO-1006',
            description='Bad dates',
            start_date=today + timedelta(days=10),
            target_date=today,
            part=self.part,
        )

        with self.assertRaises(ValidationError):
            ro.full_clean()

        # Reversed (valid) order should pass
        ro.start_date, ro.target_date = ro.target_date, ro.start_date
        ro.full_clean()

    def test_start_date_filters(self):
        """The 'has_start_date'/'start_date_before'/'start_date_after' filters should work."""
        today = datetime.now().date()

        with_start = RepairOrder.objects.create(
            reference='RO-1007',
            description='Has a start date',
            start_date=today,
            part=self.part,
        )
        without_start = RepairOrder.objects.create(
            reference='RO-1008', description='No start date', part=self.part
        )

        url = reverse('api-repair-order-list')

        response = self.get(url, {'has_start_date': True}, expected_code=200)
        pks = {item['pk'] for item in response.data}
        self.assertIn(with_start.pk, pks)
        self.assertNotIn(without_start.pk, pks)

        response = self.get(
            url,
            {'start_date_after': (today - timedelta(days=1)).isoformat()},
            expected_code=200,
        )
        pks = {item['pk'] for item in response.data}
        self.assertIn(with_start.pk, pks)
        self.assertNotIn(without_start.pk, pks)

        response = self.get(
            url,
            {'start_date_before': (today - timedelta(days=1)).isoformat()},
            expected_code=200,
        )
        pks = {item['pk'] for item in response.data}
        self.assertNotIn(with_start.pk, pks)

    def test_min_max_date_filters_include_start_date(self):
        """The 'min_date'/'max_date' calendar filters should account for start_date."""
        today = datetime.now().date()

        future_start = RepairOrder.objects.create(
            reference='RO-1009',
            description='Starts in the future',
            start_date=today + timedelta(days=30),
            part=self.part,
        )

        url = reverse('api-repair-order-list')

        # min_date in the past should still pick up an order starting in the future
        response = self.get(url, {'min_date': today.isoformat()}, expected_code=200)
        pks = {item['pk'] for item in response.data}
        self.assertIn(future_start.pk, pks)

        # max_date before the start date should exclude it
        response = self.get(url, {'max_date': today.isoformat()}, expected_code=200)
        pks = {item['pk'] for item in response.data}
        self.assertNotIn(future_start.pk, pks)

    def test_search_by_reference(self):
        """The global 'search' parameter should match against reference/description."""
        url = reverse('api-repair-order-list')

        response = self.get(url, {'search': self.ro.reference}, expected_code=200)
        pks = {item['pk'] for item in response.data}
        self.assertIn(self.ro.pk, pks)

    # ── Part field coverage ─────────────────────────────────────────

    def test_part_is_required(self):
        """'part' must be provided - both via the API and at the model level."""
        url = reverse('api-repair-order-list')

        response = self.post(
            url, {'description': 'Missing part'}, expected_code=400
        ).data
        self.assertIn('part', response)

        with self.assertRaises(ValidationError):
            RepairOrder(
                reference='RO-8888', description='No part assigned'
            ).full_clean()

    def test_part_is_immutable(self):
        """'part' cannot be changed after creation - both via the API and at the model level."""
        other_part = Part.objects.filter(assembly=True).exclude(pk=self.part.pk).first()
        assert other_part

        url = reverse('api-repair-order-detail', kwargs={'pk': self.ro.pk})
        self.patch(url, {'part': other_part.pk}, expected_code=400)
        self.ro.refresh_from_db()
        self.assertEqual(self.ro.part, self.part)

        self.ro.part = other_part
        with self.assertRaises(ValidationError):
            self.ro.full_clean()

    def test_tags(self):
        """Tags should be writable via PATCH, and only included in GET responses when requested."""
        url = reverse('api-repair-order-detail', kwargs={'pk': self.ro.pk})

        response = self.patch(url, {'tags': ['tag1', 'tag2']}, expected_code=200)
        self.assertEqual(sorted(response.data['tags']), ['tag1', 'tag2'])

        self.ro.refresh_from_db()
        self.assertEqual(self.ro.tags.count(), 2)
        self.assertEqual(sorted(t.name for t in self.ro.tags.all()), ['tag1', 'tag2'])

        # Without the 'tags' filter, a plain GET should not include tag data
        response = self.get(url, expected_code=200)
        self.assertNotIn('tags', response.data)

        response = self.get(url, {'tags': True}, expected_code=200)
        self.assertEqual(sorted(response.data['tags']), ['tag1', 'tag2'])

    def test_repair_order_part_functionality(self):
        """Verify the part FK and part_detail serializer field work end-to-end.

        Covers:
        - Creating a RepairOrder with a part assigned (via API)
        - part_detail nested serializer is returned in list responses
        - Filtering the list endpoint by part PK
        - Searching by part name
        """
        url = reverse('api-repair-order-list')

        # ── 1. Create via API with a part assigned ─────────────────
        data = self.post(
            url,
            {'description': 'Part-scoped repair order', 'part': self.part.pk},
            expected_code=201,
        ).data

        new_pk = data['pk']
        self.assertEqual(data['part'], self.part.pk)

        # ── 2. part_detail nested serializer is present ────────────
        response = self.get(url, {'part_detail': True}, expected_code=200)
        items = {item['pk']: item for item in response.data}

        # self.ro was created in setUp with self.part — verify it too
        self.assertIn(self.ro.pk, items)
        ro_data = items[self.ro.pk]
        self.assertIn('part_detail', ro_data)
        self.assertIsNotNone(ro_data['part_detail'])
        self.assertEqual(ro_data['part_detail']['pk'], self.part.pk)

        # The newly created order should also carry part_detail
        self.assertIn(new_pk, items)
        self.assertEqual(items[new_pk]['part_detail']['pk'], self.part.pk)

        # ── 3. Filter by part PK ───────────────────────────────────
        response = self.get(url, {'part': self.part.pk}, expected_code=200)
        pks = {item['pk'] for item in response.data}
        self.assertIn(self.ro.pk, pks)
        self.assertIn(new_pk, pks)

        # ── 4. Search by part name hits part__name search field ────
        response = self.get(url, {'search': self.part.name}, expected_code=200)
        pks = {item['pk'] for item in response.data}
        self.assertIn(self.ro.pk, pks)

    def test_part_filter_include_variants(self):
        """The 'part' filter should optionally include repair orders for variant parts."""
        from part.models import Part

        template = Part.objects.get(name='Chair Template')
        variant = Part.objects.filter(variant_of=template).first()
        assert variant

        variant_ro = RepairOrder.objects.create(
            reference='RO-1010', description='Repair for a variant', part=variant
        )

        url = reverse('api-repair-order-list')

        # Without 'include_variants', filtering by the template should NOT match
        response = self.get(url, {'part': template.pk}, expected_code=200)
        pks = {item['pk'] for item in response.data}
        self.assertNotIn(variant_ro.pk, pks)

        # With 'include_variants', it should
        response = self.get(
            url, {'part': template.pk, 'include_variants': True}, expected_code=200
        )
        pks = {item['pk'] for item in response.data}
        self.assertIn(variant_ro.pk, pks)

        # Filtering directly by the variant's own pk should always match, regardless
        response = self.get(url, {'part': variant.pk}, expected_code=200)
        pks = {item['pk'] for item in response.data}
        self.assertIn(variant_ro.pk, pks)

    # ── Allocation workflow ──────────────────────────────────────────

    def test_line_item_list_filters_by_order(self):
        """The line-item list endpoint must only return lines for the requested order."""
        from build.models import RepairOrderLineItem

        other_ro = RepairOrder.objects.create(
            reference='RO-7100', description='A different repair order', part=self.part
        )

        line_mine = RepairOrderLineItem.objects.create(
            order=self.ro, part=self.part, quantity=1
        )
        line_other = RepairOrderLineItem.objects.create(
            order=other_ro, part=self.part, quantity=1
        )

        url = reverse('api-repair-order-line-list')
        response = self.get(url, {'order': self.ro.pk}, expected_code=200)
        pks = {item['pk'] for item in response.data}

        self.assertIn(line_mine.pk, pks)
        self.assertNotIn(line_other.pk, pks)

    def test_allocation_list_filters_by_line(self):
        """The allocation list endpoint must only return allocations for the requested line."""
        from build.models import RepairOrderAllocation, RepairOrderLineItem
        from stock.models import StockItem, StockLocation

        p = Part.objects.filter(component=True).first()
        loc = StockLocation.objects.first()
        si = StockItem.objects.create(part=p, quantity=10, location=loc)

        line_a = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=2)
        line_b = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=2)

        alloc_a = RepairOrderAllocation.objects.create(line=line_a, item=si, quantity=1)
        alloc_b = RepairOrderAllocation.objects.create(line=line_b, item=si, quantity=1)

        url = reverse('api-repair-order-allocation-list')
        response = self.get(url, {'line': line_a.pk}, expected_code=200)
        pks = {item['pk'] for item in response.data}

        self.assertIn(alloc_a.pk, pks)
        self.assertNotIn(alloc_b.pk, pks)

    def test_line_item_allocated_quantity_annotation(self):
        """The 'allocated' field on a line item should reflect the sum of its allocations."""
        from build.models import RepairOrderAllocation, RepairOrderLineItem
        from stock.models import StockItem, StockLocation

        p = Part.objects.filter(component=True).first()
        loc = StockLocation.objects.first()
        si = StockItem.objects.create(part=p, quantity=10, location=loc)

        line = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=5)

        url = reverse('api-repair-order-line-detail', kwargs={'pk': line.pk})
        response = self.get(url, expected_code=200)
        self.assertEqual(float(response.data['allocated']), 0.0)

        RepairOrderAllocation.objects.create(line=line, item=si, quantity=3)

        response = self.get(url, expected_code=200)
        self.assertEqual(float(response.data['allocated']), 3.0)

    def test_allocation_rejects_over_commit(self):
        """An allocation cannot exceed a stock item's *unallocated* quantity.

        This accounts for quantity already committed to *other* allocations
        against the same stock item, not just its raw on-hand quantity.
        """
        from build.models import RepairOrderAllocation, RepairOrderLineItem
        from stock.models import StockItem, StockLocation

        p = Part.objects.filter(component=True).first()
        loc = StockLocation.objects.first()
        si = StockItem.objects.create(part=p, quantity=10, location=loc)

        line_a = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=8)
        line_b = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=8)

        # First allocation takes 8 of the 10 available - fine.
        RepairOrderAllocation.objects.create(line=line_a, item=si, quantity=8)

        # Second allocation against the *same* stock item requests 8 more,
        # but only 2 remain unallocated - should be rejected.
        with self.assertRaises(ValidationError):
            second = RepairOrderAllocation(line=line_b, item=si, quantity=8)
            second.full_clean()

        # Requesting only the remaining 2 should succeed.
        third = RepairOrderAllocation(line=line_b, item=si, quantity=2)
        third.full_clean()
        third.save()

    def test_allocation_rejects_changes_on_locked_order(self):
        """Allocations cannot be added or removed once the parent order is locked."""
        from build.models import RepairOrderAllocation, RepairOrderLineItem
        from stock.models import StockItem, StockLocation

        p = Part.objects.filter(component=True).first()
        loc = StockLocation.objects.first()
        si = StockItem.objects.create(part=p, quantity=10, location=loc)

        line = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=2)
        allocation = RepairOrderAllocation.objects.create(
            line=line, item=si, quantity=1
        )

        self.ro.cancel_repair()

        with self.assertRaises(ValidationError):
            RepairOrderAllocation.objects.create(line=line, item=si, quantity=1)

        with self.assertRaises(ValidationError):
            allocation.delete()

    def test_auto_allocate_stock(self):
        """POST auto-allocate/ should allocate available stock against outstanding lines."""
        from build.models import RepairOrderAllocation, RepairOrderLineItem
        from stock.models import StockItem, StockLocation

        p = Part.objects.filter(component=True).first()
        loc = StockLocation.objects.first()
        si = StockItem.objects.create(part=p, quantity=10, location=loc)

        line = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=4)

        url = reverse('api-repair-order-auto-allocate', kwargs={'pk': self.ro.pk})
        self.post(url, expected_code=201)

        total_allocated = sum(
            a.quantity for a in RepairOrderAllocation.objects.filter(line=line)
        )
        self.assertEqual(float(total_allocated), 4.0)

        si.refresh_from_db()
        # Auto-allocation only reserves stock - it does not consume it.
        self.assertEqual(float(si.quantity), 10.0)

    def test_auto_allocate_requires_role(self):
        """POST auto-allocate/ should require repair_order.add permission."""
        self.clearRoles()

        url = reverse('api-repair-order-auto-allocate', kwargs={'pk': self.ro.pk})
        self.post(url, expected_code=403)

    def test_auto_allocate_respects_source_location(self):
        """The 'location' option should restrict auto-allocation to that location (or its children)."""
        from build.models import RepairOrderAllocation, RepairOrderLineItem
        from stock.models import StockItem, StockLocation

        p = Part.objects.filter(component=True).first()
        loc_a = StockLocation.objects.create(name='Location A')
        loc_b = StockLocation.objects.create(name='Location B')

        si_a = StockItem.objects.create(part=p, quantity=10, location=loc_a)
        StockItem.objects.create(part=p, quantity=10, location=loc_b)

        line = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=4)

        url = reverse('api-repair-order-auto-allocate', kwargs={'pk': self.ro.pk})
        self.post(url, {'location': loc_a.pk}, expected_code=201)

        allocations = RepairOrderAllocation.objects.filter(line=line)
        self.assertEqual(allocations.count(), 1)
        self.assertEqual(allocations.first().item.pk, si_a.pk)

    def test_auto_allocate_excludes_location(self):
        """The 'exclude_location' option should skip stock items in that location."""
        from build.models import RepairOrderAllocation, RepairOrderLineItem
        from stock.models import StockItem, StockLocation

        p = Part.objects.filter(component=True).first()
        loc_a = StockLocation.objects.create(name='Excluded Location')
        loc_b = StockLocation.objects.create(name='Included Location')

        StockItem.objects.create(part=p, quantity=10, location=loc_a)
        si_b = StockItem.objects.create(part=p, quantity=10, location=loc_b)

        line = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=4)

        url = reverse('api-repair-order-auto-allocate', kwargs={'pk': self.ro.pk})
        self.post(url, {'exclude_location': loc_a.pk}, expected_code=201)

        allocations = RepairOrderAllocation.objects.filter(line=line)
        self.assertEqual(allocations.count(), 1)
        self.assertEqual(allocations.first().item.pk, si_b.pk)

    def test_auto_allocate_stock_sort_by(self):
        """The 'stock_sort_by' option should control which stock item is preferred."""
        from build.models import RepairOrderAllocation, RepairOrderLineItem
        from stock.models import StockItem, StockLocation

        p = Part.objects.filter(component=True).first()
        loc = StockLocation.objects.first()

        small = StockItem.objects.create(part=p, quantity=2, location=loc)
        large = StockItem.objects.create(part=p, quantity=20, location=loc)

        line = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=1)

        url = reverse('api-repair-order-auto-allocate', kwargs={'pk': self.ro.pk})
        self.post(url, {'stock_sort_by': 'quantity'}, expected_code=201)

        allocation = RepairOrderAllocation.objects.get(line=line)
        self.assertEqual(allocation.item.pk, small.pk)
        self.assertNotEqual(allocation.item.pk, large.pk)

    # ── Query count regression tests (no N+1) ───────────────────────

    def _query_count_for(self, url, params: dict) -> int:
        """Return the number of DB queries executed for a single GET request.

        Issues one throwaway request first to warm up process-level caches
        (ContentType lookups, permission role sets) that would otherwise make
        the *first* measurement in a test look artificially expensive relative
        to the second - which would mask a genuine N+1 in the comparison, or
        even flip the comparison the wrong way. Uses a generous max_query_count
        on the measured request so a genuine N+1 regression doesn't trip that
        assertion before this helper gets a chance to return the actual count.
        """
        self.get(url, params, expected_code=200, max_query_count=1000)

        with self.assertNumQueriesLessThan(1000, url=url) as context:
            self.get(url, params, expected_code=200, max_query_count=1000)
        return len(context.captured_queries)

    def test_repair_order_list_no_n_plus_one(self):
        """The order list's query count should not grow with the number of orders."""
        from company.models import Company

        customer = Company.objects.create(name='Query Count Customer', is_customer=True)

        url = reverse('api-repair-order-list')
        params = {'customer_detail': True, 'part_detail': True}

        for i in range(2):
            RepairOrder.objects.create(
                reference=f'RO-{9100 + i}',
                description='Query count test',
                customer=customer,
                part=self.part,
            )
        small_n = self._query_count_for(url, params)

        for i in range(20):
            RepairOrder.objects.create(
                reference=f'RO-{9200 + i}',
                description='Query count test',
                customer=customer,
                part=self.part,
            )
        large_n = self._query_count_for(url, params)

        self.assertEqual(small_n, large_n)

    def test_line_item_list_no_n_plus_one(self):
        """The line-item list's query count should not grow with the number of lines."""
        from build.models import RepairOrderLineItem

        parts = list(Part.objects.filter(component=True)[:5])
        url = reverse('api-repair-order-line-list')
        params = {'order': self.ro.pk, 'part_detail': True}

        for i in range(2):
            RepairOrderLineItem.objects.create(
                order=self.ro, part=parts[i % len(parts)], quantity=1
            )
        small_n = self._query_count_for(url, params)

        for i in range(20):
            RepairOrderLineItem.objects.create(
                order=self.ro, part=parts[i % len(parts)], quantity=1
            )
        large_n = self._query_count_for(url, params)

        self.assertEqual(small_n, large_n)

    def test_allocation_list_no_n_plus_one(self):
        """The allocation list's query count should not grow with the number of allocations."""
        from build.models import RepairOrderAllocation, RepairOrderLineItem
        from stock.models import StockItem, StockLocation

        p = Part.objects.filter(component=True).first()
        loc = StockLocation.objects.first()
        line = RepairOrderLineItem.objects.create(order=self.ro, part=p, quantity=100)

        url = reverse('api-repair-order-allocation-list')
        params = {'line': line.pk, 'item_detail': True}

        for _ in range(2):
            si = StockItem.objects.create(part=p, quantity=1, location=loc)
            RepairOrderAllocation.objects.create(line=line, item=si, quantity=1)
        small_n = self._query_count_for(url, params)

        for _ in range(20):
            si = StockItem.objects.create(part=p, quantity=1, location=loc)
            RepairOrderAllocation.objects.create(line=line, item=si, quantity=1)
        large_n = self._query_count_for(url, params)

        self.assertEqual(small_n, large_n)


class RepairOrderAdminTest(AdminTestCase):
    """Tests for the RepairOrder admin interface integration."""

    fixtures = ['category', 'part', 'location', 'stock']

    def test_admin(self):
        """Test the admin URL for RepairOrder."""
        part = Part.objects.filter(assembly=True).first()
        self.helper(
            model=RepairOrder,
            model_kwargs={'description': 'Admin test repair order', 'part': part},
        )
