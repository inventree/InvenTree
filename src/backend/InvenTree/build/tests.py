"""Basic unit tests for the BuildOrder app"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import tag
from django.urls import reverse

from datetime import datetime, timedelta

from InvenTree.unit_test import InvenTreeTestCase

from .models import Build
from part.models import Part, BomItem
from stock.models import StockItem

from common.settings import get_global_setting, set_global_setting
from build.status_codes import BuildStatus


class BuildTestSimple(InvenTreeTestCase):
    """Basic set of tests for the BuildOrder model functionality"""

    fixtures = [
        'category',
        'part',
        'location',
        'build',
    ]

    roles = [
        'build.change',
        'build.add',
        'build.delete',
    ]

    def test_build_objects(self):
        """Ensure the Build objects were correctly created"""
        self.assertEqual(Build.objects.count(), 5)
        b = Build.objects.get(pk=2)
        self.assertEqual(b.batch, 'B2')
        self.assertEqual(b.quantity, 21)

        self.assertEqual(str(b), 'BO-0002')

    def test_url(self):
        """Test URL lookup"""
        b1 = Build.objects.get(pk=1)
        if settings.ENABLE_CLASSIC_FRONTEND:
            self.assertEqual(b1.get_absolute_url(), '/build/1/')

    def test_is_complete(self):
        """Test build completion status"""
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
        """Test active / inactive build status"""
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

        self.assertEqual(assembly.get_bom_items().count(), 0)

        # Let's create some BOM items for this assembly
        for component in Part.objects.filter(assembly=False, component=True)[:15]:

            try:
                BomItem.objects.create(
                    part=assembly,
                    sub_part=component,
                    reference='xxx',
                    quantity=5
                )
            except ValidationError:
                pass

        # The assembly has a BOM, and is now *invalid*
        self.assertGreater(assembly.get_bom_items().count(), 0)
        self.assertFalse(assembly.is_bom_valid())

        # Create a build for an assembly with an *invalid* BOM
        set_global_setting('BUILDORDER_REQUIRE_VALID_BOM', False)
        set_global_setting('BUILDORDER_REQUIRE_ACTIVE_PART', True)

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

        # Check that expected quantity of new builds is created
        self.assertEqual(Build.objects.count(), n + 3)

class TestBuildViews(InvenTreeTestCase):
    """Tests for Build app views."""

    fixtures = [
        'category',
        'part',
        'location',
        'build',
    ]

    roles = [
        'build.change',
        'build.add',
        'build.delete',
    ]

    def setUp(self):
        """Fixturing for this suite of unit tests"""
        super().setUp()

        # Create a build output for build # 1
        self.build = Build.objects.get(pk=1)

        self.output = StockItem.objects.create(
            part=self.build.part,
            quantity=self.build.quantity,
            build=self.build,
            is_building=True,
        )

    @tag('cui')
    def test_build_index(self):
        """Test build index view."""
        response = self.client.get(reverse('build-index'))
        self.assertEqual(response.status_code, 200)

    @tag('cui')
    def test_build_detail(self):
        """Test the detail view for a Build object."""
        pk = 1

        response = self.client.get(reverse('build-detail', args=(pk,)))
        self.assertEqual(response.status_code, 200)

        build = Build.objects.get(pk=pk)

        content = str(response.content)

        self.assertIn(build.title, content)
