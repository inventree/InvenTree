from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import StockLocation


class StockLocationTest(APITestCase):
    """
    Series of API tests for the StockLocation API
    """
    list_url = reverse('api-location-list')

    def setUp(self):
        # Create a user for auth
        User = get_user_model()
        User.objects.create_user('testuser', 'test@testing.com', 'password')
        self.client.login(username='testuser', password='password')

        # Add some stock locations
        StockLocation.objects.create(name='top', description='top category')

    def test_list(self):
        # Check that we can request the StockLocation list
        response = self.client.get(self.list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_add(self):
        # Check that we can add a new StockLocation
        data = {
            'parent': 1,
            'name': 'Location',
            'description': 'Another location for stock'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class StockItemTest(APITestCase):
    """
    Series of API tests for the StockItem API
    """

    list_url = reverse('api-stock-list')

    def detail_url(self, pk):
        return reverse('api-stock-detail', kwargs={'pk': pk})

    def setUp(self):
        # Create a user for auth
        User = get_user_model()
        User.objects.create_user('testuser', 'test@testing.com', 'password')
        self.client.login(username='testuser', password='password')

        # Create some stock locations
        top = StockLocation.objects.create(name='A', description='top')

        StockLocation.objects.create(name='B', description='location b', parent=top)
        StockLocation.objects.create(name='C', description='location c', parent=top)

    def test_get_stock_list(self):
        response = self.client.get(self.list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class StocktakeTest(APITestCase):
    """
    Series of tests for the Stocktake API
    """

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'supplier_part',
        'stock',
    ]

    def setUp(self):
        User = get_user_model()
        User.objects.create_user('testuser', 'test@testing.com', 'password')
        self.client.login(username='testuser', password='password')

    def doPost(self, url, data={}):
        response = self.client.post(url, data=data, format='json')

        return response

    def test_action(self):
        """
        Test each stocktake action endpoint,
        for validation
        """

        for endpoint in ['api-stock-count', 'api-stock-add', 'api-stock-remove']:

            url = reverse(endpoint)

            data = {}

            # POST with a valid action
            response = self.doPost(url, data)
            self.assertContains(response, "must contain list", status_code=status.HTTP_400_BAD_REQUEST)

            data['items'] = [{
                'no': 'aa'
            }]

            # POST without a PK
            response = self.doPost(url, data)
            self.assertContains(response, 'must contain a valid pk', status_code=status.HTTP_400_BAD_REQUEST)

            # POST with a PK but no quantity
            data['items'] = [{
                'pk': 10
            }]
            
            response = self.doPost(url, data)
            self.assertContains(response, 'must contain a valid pk', status_code=status.HTTP_400_BAD_REQUEST)

            data['items'] = [{
                'pk': 1234
            }]

            response = self.doPost(url, data)
            self.assertContains(response, 'must contain a valid quantity', status_code=status.HTTP_400_BAD_REQUEST)

            data['items'] = [{
                'pk': 1234,
                'quantity': '10x0d'
            }]

            response = self.doPost(url, data)
            self.assertContains(response, 'must contain a valid quantity', status_code=status.HTTP_400_BAD_REQUEST)
            
            data['items'] = [{
                'pk': 1234,
                'quantity': "-1.234"
            }]
            
            response = self.doPost(url, data)
            self.assertContains(response, 'must not be less than zero', status_code=status.HTTP_400_BAD_REQUEST)

            # Test with a single item
            data = {
                'item': {
                    'pk': 1234,
                    'quantity': '10',
                }
            }

            response = self.doPost(url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
