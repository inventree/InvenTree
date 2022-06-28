"""Basic unit tests for the BuildOrder app"""


from django.core.exceptions import ValidationError
from django.urls import reverse

from datetime import datetime, timedelta

from InvenTree.helpers import InvenTreeTestCase

from common.models import InvenTreeSetting
from .models import Build
from stock.models import StockItem

from InvenTree.status_codes import BuildStatus


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

    def test_reference(self):
        """Unit tests for the BuildOrder 'reference' field"""
        pattern = 'BUILDORDER_REFERENCE_PATTERN'

        build = Build.objects.get(pk=1)

        # Simple test with wildcard matches
        InvenTreeSetting.set_setting(pattern, 'BO-[ABC]-????', None)

        # These values should pass the validator test
        for value in [
            'BO-A-1234',
            'BO-B-wxyz',
            'BO-C-----',
        ]:
            build.reference = value
            build.save()

        # These values should fail the validator test
        for value in [
            'BO-D-1234',
            'SO-A-1234',
            'BO-A-ABC',
            'BO-A-',
            'BO.A-',
        ]:
            with self.assertRaises(ValidationError):
                build.reference = value
                build.save()

        # Test for required numerical field (5 digit number)
        InvenTreeSetting.set_setting(pattern, 'BO-#####', None)

        # TODO

    def test_build_objects(self):
        """Ensure the Build objects were correctly created"""
        self.assertEqual(Build.objects.count(), 5)
        b = Build.objects.get(pk=2)
        self.assertEqual(b.batch, 'B2')
        self.assertEqual(b.quantity, 21)

        self.assertEqual(str(b), 'BO0002')

    def test_url(self):
        """Test URL lookup"""
        b1 = Build.objects.get(pk=1)
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

    def test_required_parts(self):
        """Test set of required BOM items for the build"""
        # TODO: Generate BOM for test part
        ...

    def test_cancel_build(self):
        """Test build cancellation function."""
        build = Build.objects.get(id=1)

        self.assertEqual(build.status, BuildStatus.PENDING)

        build.cancel_build(self.user)

        self.assertEqual(build.status, BuildStatus.CANCELLED)


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

    def test_build_index(self):
        """Test build index view."""
        response = self.client.get(reverse('build-index'))
        self.assertEqual(response.status_code, 200)

    def test_build_detail(self):
        """Test the detail view for a Build object."""
        pk = 1

        response = self.client.get(reverse('build-detail', args=(pk,)))
        self.assertEqual(response.status_code, 200)

        build = Build.objects.get(pk=pk)

        content = str(response.content)

        self.assertIn(build.title, content)
