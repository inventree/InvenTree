"""Unit tests for InvenTreeBarcodePlugin."""

from django.urls import reverse

import stock.models
from InvenTree.api_tester import InvenTreeAPITestCase


class TestInvenTreeBarcode(InvenTreeAPITestCase):
    """Tests for the integrated InvenTreeBarcode barcode plugin."""

    fixtures = [
        'category',
        'part',
        'location',
        'stock'
    ]

    def test_assign_errors(self):
        """Test error cases for assigment action."""

        def test_assert_error(barcode_data):
            response = self.post(
                reverse('api-barcode-link'), format='json',
                data={
                    'barcode': barcode_data,
                    'stockitem': 521
                },
                expected_code=400
            )

            self.assertIn('error', response.data)

        # test with already existing stock
        test_assert_error('{"stockitem": 521}')

        # test with already existing stock location
        test_assert_error('{"stocklocation": 7}')

        # test with already existing part location
        test_assert_error('{"part": 10004}')

    def assign(self, data, expected_code=None):
        """Peform a 'barcode assign' request"""

        return self.post(
            reverse('api-barcode-link'),
            data=data,
            expected_code=expected_code
        )

    def test_assign_to_stock_item(self):
        """Test that we can assign a unique barcode to a StockItem object"""

        # Test without providing any fields
        response = self.assign(
            {
                'barcode': 'abcde',
            },
            expected_code=400
        )

        self.assertIn('Missing data:', str(response.data))

        # Provide too many fields
        # TODO: Test this!

        bc_data = '{"blbla": 10004}'

        # Assign a barcode to a StockItem instance
        response = self.assign(
            data={
                'barcode': bc_data,
                'stockitem': 521,
            },
            expected_code=200,
        )

        data = response.data
        self.assertEqual(data['plugin'], 'InvenTreeBarcode')
        self.assertEqual(data['barcode_data'], bc_data)
        self.assertEqual(data['stockitem']['pk'], 521)

        # Check that the StockItem instance has actually been updated
        si = stock.models.StockItem.objects.get(pk=521)

        self.assertEqual(si.barcode_data, bc_data)
        self.assertEqual(si.barcode_hash, "b'\\x1b\\xe0\\xdf\\xa9%\\x82\\\\\\\\ly0\\x14I\\xe5\\x0c-'")

        # Now test that we cannot assign this barcode to something else
        response = self.assign(
            data={
                'barcode': bc_data,
                'stockitem': 1,
            },
            expected_code=400
        )

        self.assertIn('Barcode matches existing Stock Item', str(response.data))

    def test_assign_to_part(self):
        """Test that we can assign a unique barcode to a Part instance"""

        # TODO
        ...

    def test_assign_to_location(self):
        """Test that we can assign a unique barcode to a StockLocation instance"""

        # TODO
        ...

    def scan(self, data, expected_code=None):
        """Perform a 'scan' operation"""

        return self.client.post(
            reverse('api-barcode-scan'),
            data=data,
            expected_code=expected_code
        )

    def test_scan_third_party(self):
        """Test scanning of third-party barcodes"""

        # First scanned barcode is for a 'third-party' barcode (which does not exist)
        response = self.scan({'barcode': 'blbla=10004'}, expected_code=400)

        self.assertEqual(response.data['barcode_data'], 'blbla=10004')
        self.assertEqual(response.data['plugin'], None)
        self.assertEqual(response.data['error'], 'No match found for barcode data')

        # Scan for a StockItem instance
        si = stock.models.StockItem.objects.get(pk=1)

        for barcode in ['abcde', 'ABCDE', '12345']:
            si.assign_barcode(barcode_data=barcode)

            response = self.scan(
                {
                    'barcode': barcode,
                },
                expected_code=200,
            )

            self.assertIn('success', response.data)
            self.assertEqual(response.data['stockitem']['pk'], 1)

    def test_scan_inventree(self):
        """Test scanning of first-party barcodes"""

        # Scan a StockItem object (which does not exist)
        response = self.scan(
            {
                'barcode': '{"stockitem": 5}',
            },
            expected_code=400,
        )

        self.assertIn('Stock item does not exist', str(response.data))

        # Scan a StockItem object (which does exist)
        response = self.scan(
            {
                'barcode': '{"stockitem": 1}',
            },
            expected_code=200
        )

        self.assertIn('success', response.data)
        self.assertIn('stockitem', response.data)
        self.assertEqual(response.data['stockitem']['pk'], 1)

        # Scan a StockLocation object
        response = self.scan(
            {
                'barcode': '{"stocklocation": 5}',
            },
            expected_code=200,
        )

        self.assertEqual(response.data['plugin'], 'InvenTreeBarcode')
        self.assertIn('success', response.data)
        self.assertEqual(response.data['stocklocation']['pk'], 5)

        # Scan a Part object
        response = self.scan(
            {
                'barcode': '{"part": 5}'
            },
            expected_code=200,
        )

        self.assertEqual(response.data['part']['pk'], 5)
