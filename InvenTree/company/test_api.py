from django.urls import reverse

from rest_framework import status

from InvenTree.api_tester import InvenTreeAPITestCase

from .models import Company


class CompanyTest(InvenTreeAPITestCase):
    """Series of tests for the Company DRF API."""

    roles = [
        'purchase_order.add',
        'purchase_order.change',
    ]

    def setUp(self):

        super().setUp()

        self.acme = Company.objects.create(name='ACME', description='Supplier', is_customer=False, is_supplier=True)
        Company.objects.create(name='Drippy Cup Co.', description='Customer', is_customer=True, is_supplier=False)
        Company.objects.create(name='Sippy Cup Emporium', description='Another supplier')

    def test_company_list(self):
        url = reverse('api-company-list')

        # There should be three companies
        response = self.get(url)
        self.assertEqual(len(response.data), 3)

        data = {'is_customer': True}

        # There should only be one customer
        response = self.get(url, data)
        self.assertEqual(len(response.data), 1)

        data = {'is_supplier': True}

        # There should be two suppliers
        response = self.get(url, data)
        self.assertEqual(len(response.data), 2)

    def test_company_detail(self):
        """Tests for the Company detail endpoint."""
        url = reverse('api-company-detail', kwargs={'pk': self.acme.pk})
        response = self.get(url)

        self.assertEqual(response.data['name'], 'ACME')

        # Change the name of the company
        # Note we should not have the correct permissions (yet)
        data = response.data
        response = self.client.patch(url, data, format='json', expected_code=400)

        self.assignRole('company.change')

        # Update the name and set the currency to a valid value
        data['name'] = 'ACMOO'
        data['currency'] = 'NZD'

        response = self.client.patch(url, data, format='json', expected_code=200)

        self.assertEqual(response.data['name'], 'ACMOO')
        self.assertEqual(response.data['currency'], 'NZD')

    def test_company_search(self):
        """Test search functionality in company list."""
        url = reverse('api-company-list')
        data = {'search': 'cup'}
        response = self.get(url, data)
        self.assertEqual(len(response.data), 2)

    def test_company_create(self):
        """Test that we can create a company via the API!"""
        url = reverse('api-company-list')

        # Name is required
        response = self.post(
            url,
            {
                'description': 'A description!',
            },
            expected_code=400
        )

        # Minimal example, checking default values
        response = self.post(
            url,
            {
                'name': 'My API Company',
                'description': 'A company created via the API',
            },
            expected_code=201
        )

        self.assertTrue(response.data['is_supplier'])
        self.assertFalse(response.data['is_customer'])
        self.assertFalse(response.data['is_manufacturer'])

        self.assertEqual(response.data['currency'], 'USD')

        # Maximal example, specify values
        response = self.post(
            url,
            {
                'name': "Another Company",
                'description': "Also created via the API!",
                'currency': 'AUD',
                'is_supplier': False,
                'is_manufacturer': True,
                'is_customer': True,
            },
            expected_code=201
        )

        self.assertEqual(response.data['currency'], 'AUD')
        self.assertFalse(response.data['is_supplier'])
        self.assertTrue(response.data['is_customer'])
        self.assertTrue(response.data['is_manufacturer'])

        # Attempt to create with invalid currency
        response = self.post(
            url,
            {
                'name': "A name",
                'description': 'A description',
                'currency': 'POQD',
            },
            expected_code=400
        )

        self.assertTrue('currency' in response.data)


class ManufacturerTest(InvenTreeAPITestCase):
    """Series of tests for the Manufacturer DRF API."""

    fixtures = [
        'category',
        'part',
        'location',
        'company',
        'manufacturer_part',
    ]

    roles = [
        'part.add',
        'part.change',
    ]

    def test_manufacturer_part_list(self):
        url = reverse('api-manufacturer-part-list')

        # There should be three manufacturer parts
        response = self.get(url)
        self.assertEqual(len(response.data), 3)

        # Create manufacturer part
        data = {
            'part': 1,
            'manufacturer': 7,
            'MPN': 'MPN_TEST',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['MPN'], 'MPN_TEST')

        # Filter by manufacturer
        data = {'manufacturer': 7}
        response = self.get(url, data)
        self.assertEqual(len(response.data), 3)

        # Filter by part
        data = {'part': 5}
        response = self.get(url, data)
        self.assertEqual(len(response.data), 2)

    def test_manufacturer_part_detail(self):
        """Tests for the ManufacturerPart detail endpoint."""
        url = reverse('api-manufacturer-part-detail', kwargs={'pk': 1})

        response = self.get(url)
        self.assertEqual(response.data['MPN'], 'MPN123')

        # Change the MPN
        data = {
            'MPN': 'MPN-TEST-123',
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['MPN'], 'MPN-TEST-123')

    def test_manufacturer_part_search(self):
        # Test search functionality in manufacturer list
        url = reverse('api-manufacturer-part-list')
        data = {'search': 'MPN'}
        response = self.get(url, data)
        self.assertEqual(len(response.data), 3)

    def test_supplier_part_create(self):
        url = reverse('api-supplier-part-list')

        # Create a manufacturer part
        response = self.post(
            reverse('api-manufacturer-part-list'),
            {
                'part': 1,
                'manufacturer': 7,
                'MPN': 'PART_NUMBER',
            },
            expected_code=201
        )

        pk = response.data['pk']

        # Create a supplier part (associated with the new manufacturer part)
        data = {
            'part': 1,
            'supplier': 1,
            'SKU': 'SKU_TEST',
            'manufacturer_part': pk,
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check manufacturer part
        manufacturer_part_id = int(response.data['manufacturer_part_detail']['pk'])
        url = reverse('api-manufacturer-part-detail', kwargs={'pk': manufacturer_part_id})
        response = self.get(url)
        self.assertEqual(response.data['MPN'], 'PART_NUMBER')
