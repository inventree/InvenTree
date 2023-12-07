"""Unit tests for Barcode endpoints."""

from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from stock.models import StockItem


class BarcodeAPITest(InvenTreeAPITestCase):
    """Tests for barcode api."""

    fixtures = [
        'category',
        'part',
        'location',
        'stock'
    ]

    def setUp(self):
        """Setup for all tests."""
        super().setUp()

        self.scan_url = reverse('api-barcode-scan')
        self.assign_url = reverse('api-barcode-link')
        self.unassign_url = reverse('api-barcode-unlink')

    def postBarcode(self, url, barcode, expected_code=None):
        """Post barcode and return results."""
        return self.post(url, format='json', data={'barcode': str(barcode)}, expected_code=expected_code)

    def test_invalid(self):
        """Test that invalid requests fail."""
        # test scan url
        self.post(self.scan_url, format='json', data={}, expected_code=400)

        # test wrong assign urls
        self.post(self.assign_url, format='json', data={}, expected_code=400)
        self.post(self.assign_url, format='json', data={'barcode': '123'}, expected_code=400)
        self.post(self.assign_url, format='json', data={'barcode': '123', 'stockitem': '123'}, expected_code=400)

    def test_empty(self):
        """Test an empty barcode scan.

        Ensure that all required data is in the response.
        """
        response = self.postBarcode(self.scan_url, '', expected_code=400)

        data = response.data
        self.assertIn('barcode', data)

        self.assertIn('This field may not be blank', str(response.data['barcode']))

    def test_find_part(self):
        """Test that we can lookup a part based on ID."""

        part = Part.objects.first()

        response = self.post(
            self.scan_url,
            {
                'barcode': f'{{"part": {part.pk}}}',
            },
            expected_code=200
        )

        self.assertIn('part', response.data)
        self.assertIn('barcode_data', response.data)
        self.assertEqual(response.data['part']['pk'], part.pk)

    def test_invalid_part(self):
        """Test response for invalid part."""
        response = self.post(
            self.scan_url,
            {
                'barcode': '{"part": 999999999}'
            },
            expected_code=400
        )

        self.assertIn('error', response.data)

    def test_find_stock_item(self):
        """Test that we can lookup a stock item based on ID."""

        item = StockItem.objects.first()

        response = self.post(
            self.scan_url,
            {
                'barcode': item.format_barcode(),
            },
            expected_code=200
        )

        self.assertIn('stockitem', response.data)
        self.assertIn('barcode_data', response.data)
        self.assertEqual(response.data['stockitem']['pk'], item.pk)

    def test_invalid_item(self):
        """Test response for invalid stock item."""
        response = self.post(
            self.scan_url,
            {
                'barcode': '{"stockitem": 999999999}'
            },
            expected_code=400
        )

        self.assertIn('error', response.data)

    def test_find_location(self):
        """Test that we can lookup a stock location based on ID."""
        response = self.post(
            self.scan_url,
            {
                'barcode': '{"stocklocation": 1}',
            },
            expected_code=200
        )

        self.assertIn('stocklocation', response.data)
        self.assertIn('barcode_data', response.data)
        self.assertEqual(response.data['stocklocation']['pk'], 1)

    def test_invalid_location(self):
        """Test response for an invalid location."""
        response = self.post(
            self.scan_url,
            {
                'barcode': '{"stocklocation": 999999999}'
            },
            expected_code=400
        )

        self.assertIn('error', response.data)

    def test_integer_barcode(self):
        """Test scan of an integer barcode."""
        response = self.postBarcode(self.scan_url, '123456789', expected_code=400)

        data = response.data
        self.assertIn('error', data)

    def test_array_barcode(self):
        """Test scan of barcode with string encoded array."""
        response = self.postBarcode(self.scan_url, "['foo', 'bar']", expected_code=400)

        data = response.data
        self.assertIn('error', data)

    def test_barcode_generation(self):
        """Test that a barcode is generated with a scan."""
        item = StockItem.objects.get(pk=522)

        response = self.postBarcode(self.scan_url, item.format_barcode(), expected_code=200)
        data = response.data

        self.assertIn('stockitem', data)

        pk = data['stockitem']['pk']

        self.assertEqual(pk, item.pk)

    def test_association(self):
        """Test that a barcode can be associated with a StockItem."""
        item = StockItem.objects.get(pk=522)

        self.assignRole('stock.change')

        self.assertEqual(len(item.barcode_hash), 0)

        barcode_data = 'A-TEST-BARCODE-STRING'

        response = self.post(
            self.assign_url, format='json',
            data={
                'barcode': barcode_data,
                'stockitem': item.pk
            },
            expected_code=200
        )

        data = response.data

        self.assertIn('success', data)

        result_hash = data['barcode_hash']

        # Read the item out from the database again
        item.refresh_from_db()

        self.assertEqual(item.barcode_data, barcode_data)
        self.assertEqual(result_hash, item.barcode_hash)

        # Ensure that the same barcode hash cannot be assigned to a different stock item!
        response = self.post(
            self.assign_url, format='json',
            data={
                'barcode': barcode_data,
                'stockitem': 521
            },
            expected_code=400
        )

        self.assertIn('error', response.data)
        self.assertNotIn('success', response.data)

        # Check that we can now unassign a barcode
        response = self.post(
            self.unassign_url,
            {
                'stockitem': item.pk,
            },
            expected_code=200
        )

        item.refresh_from_db()
        self.assertEqual(item.barcode_data, '')

        # Check that the 'unassign' endpoint fails if the stockitem is invalid
        response = self.post(
            self.unassign_url,
            {
                'stockitem': 999999999,
            },
            expected_code=400
        )

    def test_unassign_endpoint(self):
        """Test that the unassign endpoint works as expected"""

        invalid_keys = ['cat', 'dog', 'fish']

        # Invalid key should fail
        for k in invalid_keys:
            response = self.post(
                self.unassign_url,
                {
                    k: 123
                },
                expected_code=400
            )

            self.assertIn("Missing data: Provide one of", str(response.data['error']))

        valid_keys = ['build', 'salesorder', 'part']

        # Valid key but invalid pk should fail
        for k in valid_keys:
            response = self.post(
                self.unassign_url,
                {
                    k: 999999999
                },
                expected_code=400
            )

            self.assertIn("object does not exist", str(response.data[k]))
