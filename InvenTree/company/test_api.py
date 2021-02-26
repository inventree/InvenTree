from rest_framework import status
from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase

from .models import Company


class CompanyTest(InvenTreeAPITestCase):
    """
    Series of tests for the Company DRF API
    """

    roles = [
        'purchase_order.add',
        'purchase_order.change',
    ]

    def setUp(self):

        super().setUp()

        Company.objects.create(name='ACME', description='Supplier', is_customer=False, is_supplier=True)
        Company.objects.create(name='Drippy Cup Co.', description='Customer', is_customer=True, is_supplier=False)
        Company.objects.create(name='Sippy Cup Emporium', description='Another supplier')

    def test_company_list(self):
        url = reverse('api-company-list')

        # There should be two companies
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
        url = reverse('api-company-detail', kwargs={'pk': 1})
        response = self.get(url)

        self.assertEqual(response.data['name'], 'ACME')

        # Change the name of the company
        data = response.data
        data['name'] = 'ACMOO'
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'ACMOO')

    def test_company_search(self):
        # Test search functionality in company list
        url = reverse('api-company-list')
        data = {'search': 'cup'}
        response = self.get(url, data)
        self.assertEqual(len(response.data), 2)
