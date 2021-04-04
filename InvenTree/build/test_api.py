# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.urls import reverse

from part.models import Part
from build.models import Build

from InvenTree.status_codes import BuildStatus
from InvenTree.api_tester import InvenTreeAPITestCase


class BuildAPITest(InvenTreeAPITestCase):
    """
    Series of tests for the Build DRF API
    """

    fixtures = [
        'category',
        'part',
        'location',
        'bom',
        'build',
    ]

    # Required roles to access Build API endpoints
    roles = [
        'build.change',
        'build.add'
    ]
    
    def setUp(self):

        super().setUp()


class BuildListTest(BuildAPITest):
    """
    Tests for the BuildOrder LIST API
    """

    url = reverse('api-build-list')

    def test_get_all_builds(self):
        """
        Retrieve *all* builds via the API
        """

        builds = self.get(self.url)

        self.assertEqual(len(builds.data), 5)

        builds = self.get(self.url, data={'active': True})
        self.assertEqual(len(builds.data), 1)
        
        builds = self.get(self.url, data={'status': BuildStatus.COMPLETE})
        self.assertEqual(len(builds.data), 4)

        builds = self.get(self.url, data={'overdue': False})
        self.assertEqual(len(builds.data), 5)

        builds = self.get(self.url, data={'overdue': True})
        self.assertEqual(len(builds.data), 0)

    def test_overdue(self):
        """
        Create a new build, in the past
        """

        in_the_past = datetime.now().date() - timedelta(days=50)

        part = Part.objects.get(pk=50)

        Build.objects.create(
            part=part,
            quantity=10,
            title='Just some thing',
            status=BuildStatus.PRODUCTION,
            target_date=in_the_past
        )

        response = self.get(self.url, data={'overdue': True})

        builds = response.data

        self.assertEqual(len(builds), 1)

    def test_sub_builds(self):
        """
        Test the build / sub-build relationship
        """

        parent = Build.objects.get(pk=5)

        part = Part.objects.get(pk=50)

        n = Build.objects.count()

        # Make some sub builds
        for i in range(5):
            Build.objects.create(
                part=part,
                quantity=10,
                reference=f"build-000{i}",
                title=f"Sub build {i}",
                parent=parent
            )

        # And some sub-sub builds
        for sub_build in Build.objects.filter(parent=parent):

            for i in range(3):
                Build.objects.create(
                    part=part,
                    reference=f"{sub_build.reference}-00{i}-sub",
                    quantity=40,
                    title=f"sub sub build {i}",
                    parent=sub_build
                )

        # 20 new builds should have been created!
        self.assertEqual(Build.objects.count(), (n + 20))

        Build.objects.rebuild()

        # Search by parent
        response = self.get(self.url, data={'parent': parent.pk})

        builds = response.data

        self.assertEqual(len(builds), 5)

        # Search by ancestor
        response = self.get(self.url, data={'ancestor': parent.pk})

        builds = response.data

        self.assertEqual(len(builds), 20)
