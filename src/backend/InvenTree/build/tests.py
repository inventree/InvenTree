"""Basic unit tests for the BuildOrder app."""

from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.urls import reverse

from build.status_codes import BuildStatus, RepairOrderStatus
from common.settings import set_global_setting
from InvenTree.unit_test import InvenTreeAPITestCase, InvenTreeTestCase
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

    def test_repair_order_lifecycle(self):
        """Walk a RepairOrder through a full lifecycle.

        PENDING → IN_PROGRESS → ON_HOLD → IN_PROGRESS → COMPLETE.
        Exercises issue_repair, hold_repair, and complete_repair.
        """
        ro = RepairOrder.objects.create(
            reference='RO-LIFE-001', description='Lifecycle test repair order'
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
            reference='RO-CANC-001', description='Cancel lifecycle test repair order'
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
        """Create a RepairOrder for tests to act on."""
        super().setUp()

        # Grant repair_order add/change/delete so most tests pass.
        # Individual tests that check permission denial will remove roles first.
        self.assignRole('repair_order.add')
        self.assignRole('repair_order.change')
        self.assignRole('repair_order.delete')
        self.assignRole('repair_order.view')

        self.ro = RepairOrder.objects.create(
            reference='RO-API-001', description='API test repair order'
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
            url, {'description': 'Created via API'}, expected_code=201
        ).data

        self.assertIn('pk', data)
        self.assertEqual(data['status'], RepairOrderStatus.PENDING.value)

    # ── Serializer validation ──────────────────────────────────────

    def test_status_is_read_only(self):
        """PATCH should not allow direct status changes (read-only field)."""
        url = reverse('api-repair-order-detail', kwargs={'pk': self.ro.pk})
        self.patch(url, {'status': RepairOrderStatus.COMPLETE.value}, expected_code=200)
        self.ro.refresh_from_db()
        # Status must NOT have changed — it's read-only
        self.assertEqual(self.ro.status, RepairOrderStatus.PENDING.value)

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
        # Complete the order
        self.ro.complete_repair()
        self.ro.save()

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

        # Complete the order (consumes stock)
        self.ro.issue_repair()
        self.ro.complete_repair(user=self.user)
        self.ro.save()

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

        # Cancel the order
        self.ro.cancel_repair()
        self.ro.save()

        si.refresh_from_db()
        # Stock should NOT have been consumed
        self.assertEqual(float(si.quantity), original_qty)

        # Allocations should be deleted
        self.assertEqual(
            RepairOrderAllocation.objects.filter(line__order=self.ro).count(), 0
        )
