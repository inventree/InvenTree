from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from InvenTree.helpers import addUserPermissions

from .models import Company


class CompanyTest(APITestCase):
    """
    Series of tests for the Company DRF API
    """

    def setUp(self):
        # Create a user for auth
        user = get_user_model()
        self.user = user.objects.create_user('testuser', 'test@testing.com', 'password')
        
        perms = [
            'view_company',
            'change_company',
            'add_company',
        ]

        addUserPermissions(self.user, perms)
        
        self.client.login(username='testuser', password='password')

        Company.objects.create(name='ACME', description='Supplier', is_customer=False, is_supplier=True)
        Company.objects.create(name='Drippy Cup Co.', description='Customer', is_customer=True, is_supplier=False)
        Company.objects.create(name='Sippy Cup Emporium', description='Another supplier')

    def test_company_list(self):
        url = reverse('api-company-list')

        # There should be two companies
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 3)

        data = {'is_customer': True}

        # There should only be one customer
        response = self.client.get(url, data, format='json')
        self.assertEqual(len(response.data), 1)

        data = {'is_supplier': True}

        # There should be two suppliers
        response = self.client.get(url, data, format='json')
        self.assertEqual(len(response.data), 2)

    def test_company_detail(self):
        url = reverse('api-company-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')

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
        response = self.client.get(url, data, format='json')
        self.assertEqual(len(response.data), 2)
