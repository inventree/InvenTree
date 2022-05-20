from django.urls import reverse

from datetime import datetime, timedelta

from InvenTree.helpers import InvenTreeTestCase

from .models import Build
from stock.models import StockItem

from InvenTree.status_codes import BuildStatus


class BuildTestSimple(InvenTreeTestCase):

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
        # Ensure the Build objects were correctly created
        self.assertEqual(Build.objects.count(), 5)
        b = Build.objects.get(pk=2)
        self.assertEqual(b.batch, 'B2')
        self.assertEqual(b.quantity, 21)

        self.assertEqual(str(b), 'BO0002')

    def test_url(self):
        b1 = Build.objects.get(pk=1)
        self.assertEqual(b1.get_absolute_url(), '/build/1/')

    def test_is_complete(self):
        b1 = Build.objects.get(pk=1)
        b2 = Build.objects.get(pk=2)

        self.assertEqual(b1.is_complete, False)
        self.assertEqual(b2.is_complete, True)

        self.assertEqual(b2.status, BuildStatus.COMPLETE)

    def test_overdue(self):
        """
        Test overdue status functionality
        """

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
        b1 = Build.objects.get(pk=1)
        b2 = Build.objects.get(pk=2)

        self.assertEqual(b1.is_active, True)
        self.assertEqual(b2.is_active, False)

    def test_required_parts(self):
        # TODO - Generate BOM for test part
        pass

    def test_cancel_build(self):
        """ Test build cancellation function """

        build = Build.objects.get(id=1)

        self.assertEqual(build.status, BuildStatus.PENDING)

        build.cancel_build(self.user)

        self.assertEqual(build.status, BuildStatus.CANCELLED)


class TestBuildViews(InvenTreeTestCase):
    """ Tests for Build app views """

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
        """ test build index view """

        response = self.client.get(reverse('build-index'))
        self.assertEqual(response.status_code, 200)

    def test_build_detail(self):
        """ Test the detail view for a Build object """

        pk = 1

        response = self.client.get(reverse('build-detail', args=(pk,)))
        self.assertEqual(response.status_code, 200)

        build = Build.objects.get(pk=pk)

        content = str(response.content)

        self.assertIn(build.title, content)
