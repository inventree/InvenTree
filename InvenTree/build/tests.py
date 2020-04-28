# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase
from rest_framework import status

import json

from .models import Build

from InvenTree.status_codes import BuildStatus


class BuildTestSimple(TestCase):

    fixtures = [
        'category',
        'part',
        'location',
        'build',
    ]

    def setUp(self):
        # Create a user for auth
        User = get_user_model()
        User.objects.create_user('testuser', 'test@testing.com', 'password')

        self.user = User.objects.get(username='testuser')
        self.client.login(username='testuser', password='password')

    def test_build_objects(self):
        # Ensure the Build objects were correctly created
        self.assertEqual(Build.objects.count(), 2)
        b = Build.objects.get(pk=2)
        self.assertEqual(b.batch, 'B2')
        self.assertEqual(b.quantity, 21)

        self.assertEqual(str(b), '21 x Orphan')

    def test_url(self):
        b1 = Build.objects.get(pk=1)
        self.assertEqual(b1.get_absolute_url(), '/build/1/')

    def test_is_complete(self):
        b1 = Build.objects.get(pk=1)
        b2 = Build.objects.get(pk=2)

        self.assertEqual(b1.is_complete, False)
        self.assertEqual(b2.is_complete, True)

        self.assertEqual(b2.status, BuildStatus.COMPLETE)

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

        build.cancelBuild(self.user)

        self.assertEqual(build.status, BuildStatus.CANCELLED)


class TestBuildAPI(APITestCase):
    """
    Series of tests for the Build DRF API
    - Tests for Build API
    - Tests for BuildItem API
    """

    fixtures = [
        'category',
        'part',
        'location',
        'build',
    ]

    def setUp(self):
        # Create a user for auth
        User = get_user_model()
        User.objects.create_user('testuser', 'test@testing.com', 'password')

        self.client.login(username='testuser', password='password')

    def test_get_build_list(self):
        """ Test that we can retrieve list of build objects """
        url = reverse('api-build-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_build_item_list(self):
        """ Test that we can retrieve list of BuildItem objects """
        url = reverse('api-build-item-list')

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test again, filtering by park ID
        response = self.client.get(url, {'part': '1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestBuildViews(TestCase):
    """ Tests for Build app views """

    fixtures = [
        'category',
        'part',
        'location',
        'build',
    ]

    def setUp(self):
        super().setUp()

        # Create a user
        User = get_user_model()
        User.objects.create_user('username', 'user@email.com', 'password')

        self.client.login(username='username', password='password')

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
    
    def test_build_create(self):
        """ Test the build creation view (ajax form) """

        url = reverse('build-create')

        # Create build without specifying part
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
    
        # Create build with valid part
        response = self.client.get(url, {'part': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Create build with invalid part
        response = self.client.get(url, {'part': 9999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_build_allocate(self):
        """ Test the part allocation view for a Build """

        url = reverse('build-allocate', args=(1,))

        # Get the page normally
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Get the page in editing mode
        response = self.client.get(url, {'edit': 1})
        self.assertEqual(response.status_code, 200)
    
    def test_build_item_create(self):
        """ Test the BuildItem creation view (ajax form) """

        url = reverse('build-item-create')

        # Try without a part specified
        response = self.client.get(url, {'build': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Try with an invalid build ID
        response = self.client.get(url, {'build': 9999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Try with a valid part specified
        response = self.client.get(url, {'build': 1, 'part': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Try with an invalid part specified
        response = self.client.get(url, {'build': 1, 'part': 9999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_build_item_edit(self):
        """ Test the BuildItem edit view (ajax form) """
        
        # TODO
        # url = reverse('build-item-edit')
        pass

    def test_build_complete(self):
        """ Test the build completion form """

        url = reverse('build-complete', args=(1,))

        # Test without confirmation
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertFalse(data['form_valid'])

        # Test with confirmation, valid location
        response = self.client.post(url, {'confirm': 1, 'location': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['form_valid'])

        # Test with confirmation, invalid location
        response = self.client.post(url, {'confirm': 1, 'location': 9999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertFalse(data['form_valid'])

    def test_build_cancel(self):
        """ Test the build cancellation form """

        url = reverse('build-cancel', args=(1,))

        # Test without confirmation
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertFalse(data['form_valid'])

        b = Build.objects.get(pk=1)
        self.assertEqual(b.status, 10)  # Build status is still PENDING

        # Test with confirmation
        response = self.client.post(url, {'confirm_cancel': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['form_valid'])

        b = Build.objects.get(pk=1)
        self.assertEqual(b.status, 30)  # Build status is now CANCELLED

    def test_build_unallocate(self):
        """ Test the build unallocation view (ajax form) """

        url = reverse('build-unallocate', args=(1,))

        # Test without confirmation
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertFalse(data['form_valid'])
        
        # Test with confirmation
        response = self.client.post(url, {'confirm': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['form_valid'])
