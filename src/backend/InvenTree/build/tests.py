"""Basic unit tests for the BuildOrder app."""

from datetime import datetime, timedelta

from django.core.exceptions import ValidationError

from build.status_codes import BuildStatus
from common.settings import set_global_setting
from InvenTree.unit_test import InvenTreeTestCase
from part.models import BomItem, Part

from .models import Build


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
