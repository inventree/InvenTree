# -*- coding: utf-8 -*-

"""
Unit tests for Barcode endpoints
"""

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from stock.models import StockItem


class BarcodeAPITest(APITestCase):

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

        self.scan_url = reverse('api-barcode-scan')
        self.assign_url = reverse('api-barcode-link')

    def postBarcode(self, url, barcode):

        return self.client.post(url, format='json', data={'barcode': str(barcode)})

    def test_invalid(self):

        # test scan url
        response = self.client.post(self.scan_url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # test wrong assign urls
        response = self.client.post(self.assign_url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.assign_url, format='json', data={'barcode': '123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.assign_url, format='json', data={'barcode': '123', 'stockitem': '123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty(self):

        response = self.postBarcode(self.scan_url, '')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn('error', data)

        self.assertIn('barcode_data', data)
        self.assertIn('hash', data)
        self.assertIn('plugin', data)
        self.assertIsNone(data['plugin'])

    def test_find_part(self):
        """
        Test that we can lookup a part based on ID
        """

        response = self.client.post(
            self.scan_url,
            {
                'barcode': {
                    'part': 1,
                },
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('part', response.data)
        self.assertIn('barcode_data', response.data)
        self.assertEqual(response.data['part']['pk'], 1)

    def test_find_stock_item(self):
        """
        Test that we can lookup a stock item based on ID
        """

        response = self.client.post(
            self.scan_url,
            {
                'barcode': {
                    'stockitem': 1,
                }
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stockitem', response.data)
        self.assertIn('barcode_data', response.data)
        self.assertEqual(response.data['stockitem']['pk'], 1)

    def test_find_location(self):
        """
        Test that we can lookup a stock location based on ID
        """

        response = self.client.post(
            self.scan_url,
            {
                'barcode': {
                    'stocklocation': 1,
                },
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stocklocation', response.data)
        self.assertIn('barcode_data', response.data)
        self.assertEqual(response.data['stocklocation']['pk'], 1)

    def test_integer_barcode(self):

        response = self.postBarcode(self.scan_url, '123456789')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn('error', data)

        self.assertIn('barcode_data', data)
        self.assertIn('hash', data)
        self.assertIn('plugin', data)
        self.assertIsNone(data['plugin'])

    def test_array_barcode(self):

        response = self.postBarcode(self.scan_url, "['foo', 'bar']")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn('error', data)

        self.assertIn('barcode_data', data)
        self.assertIn('hash', data)
        self.assertIn('plugin', data)
        self.assertIsNone(data['plugin'])

    def test_barcode_generation(self):

        item = StockItem.objects.get(pk=522)

        response = self.postBarcode(self.scan_url, item.format_barcode())
        data = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('stockitem', data)

        pk = data['stockitem']['pk']

        self.assertEqual(pk, item.pk)

    def test_association(self):
        """
        Test that a barcode can be associated with a StockItem
        """

        item = StockItem.objects.get(pk=522)

        self.assertEqual(len(item.uid), 0)

        barcode_data = 'A-TEST-BARCODE-STRING'

        response = self.client.post(
            self.assign_url, format='json',
            data={
                'barcode': barcode_data,
                'stockitem': item.pk
            }
        )

        data = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('success', data)

        result_hash = data['hash']

        # Read the item out from the database again
        item = StockItem.objects.get(pk=522)

        self.assertEqual(result_hash, item.uid)

        # Ensure that the same UID cannot be assigned to a different stock item!
        response = self.client.post(
            self.assign_url, format='json',
            data={
                'barcode': barcode_data,
                'stockitem': 521
            }
        )

        data = response.data

        self.assertIn('error', data)
        self.assertNotIn('success', data)


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
