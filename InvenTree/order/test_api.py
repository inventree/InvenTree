"""
Tests for the Order API
"""

from rest_framework.test import APITestCase
from rest_framework import status

from django.urls import reverse
from django.contrib.auth import get_user_model


class OrderTest(APITestCase):

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'supplier_part',
        'stock',
    ]

    def setUp(self):

        # Create a user for auth
        get_user_model().objects.create_user('testuser', 'test@testing.com', 'password')
        self.client.login(username='testuser', password='password')

    def doGet(self, url, options=''):

        return self.client.get(url + "?" + options, format='json')

    def test_po_list(self):
        
        url = reverse('api-po-list')

        # List all order items
        response = self.doGet(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Filter by stuff
        response = self.doGet(url, 'status=10&part=1&supplier_part=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_po_attachments(self):

        url = reverse('api-po-attachment-list')

        response = self.doGet(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_so_attachments(self):

        url = reverse('api-so-attachment-list')

        response = self.doGet(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
