# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, timedelta

from rest_framework.test import APITestCase

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from part.models import Part
from build.models import Build

from InvenTree.status_codes import BuildStatus


class BuildAPITest(APITestCase):
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
    
    def setUp(self):
        # Create a user for auth
        user = get_user_model()
        
        self.user = user.objects.create_user(
            username='testuser',
            email='test@testing.com',
            password='password'
        )

        # Put the user into a group with the correct permissions
        group = Group.objects.create(name='mygroup')
        self.user.groups.add(group)

        # Give the group *all* the permissions!
        for rule in group.rule_sets.all():
            rule.can_view = True
            rule.can_change = True
            rule.can_add = True
            rule.can_delete = True

            rule.save()

        group.save()

        self.client.login(username='testuser', password='password')


class BuildListTest(BuildAPITest):
    """
    Tests for the BuildOrder LIST API
    """

    url = reverse('api-build-list')

    def get(self, status_code=200, data={}):

        response = self.client.get(self.url, data, format='json')

        self.assertEqual(response.status_code, status_code)

        return response.data

    def test_get_all_builds(self):
        """
        Retrieve *all* builds via the API
        """

        builds = self.get()

        self.assertEqual(len(builds), 5)

        builds = self.get(data={'active': True})
        self.assertEqual(len(builds), 1)
        
        builds = self.get(data={'status': BuildStatus.COMPLETE})
        self.assertEqual(len(builds), 4)

        builds = self.get(data={'overdue': False})
        self.assertEqual(len(builds), 5)

        builds = self.get(data={'overdue': True})
        self.assertEqual(len(builds), 0)

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

        builds = self.get(data={'overdue': True})

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
        builds = self.get(data={'parent': parent.pk})

        self.assertEqual(len(builds), 5)

        # Search by ancestor
        builds = self.get(data={'ancestor': parent.pk})

        self.assertEqual(len(builds), 20)
