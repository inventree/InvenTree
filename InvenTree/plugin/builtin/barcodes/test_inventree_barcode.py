# -*- coding: utf-8 -*-
"""Unit tests for InvenTreeBarcodePlugin"""

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status


class TestInvenTreeBarcode(APITestCase):

    fixtures = [
        'category',
        'part',
        'location',
        'stock'
    ]

    def setUp(self):
        # Create a user for auth
        user = get_user_model()
        user.objects.create_user('testuser', 'test@testing.com', 'password')

        self.client.login(username='testuser', password='password')

    def test_errors(self):
        """
        Test all possible error cases for assigment action
        """

        def test_assert_error(barcode_data):
            response = self.client.post(
                reverse('api-barcode-link'), format='json',
                data={
                    'barcode': barcode_data,
                    'stockitem': 521
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('error', response.data)

        # test with already existing stock
        test_assert_error('{"stockitem": 521}')

        # test with already existing stock location
        test_assert_error('{"stocklocation": 7}')

        # test with already existing part location
        test_assert_error('{"part": 10004}')

        # test with hash
        test_assert_error('{"blbla": 10004}')

    def test_scan(self):
        """
        Test that a barcode can be scanned
        """

        response = self.client.post(reverse('api-barcode-scan'), format='json', data={'barcode': 'blbla=10004'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
