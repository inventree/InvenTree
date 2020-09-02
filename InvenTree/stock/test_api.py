from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import StockLocation


class StockAPITestCase(APITestCase):

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'supplier_part',
        'stock',
        'stock_tests',
    ]

    def setUp(self):
        # Create a user for auth
        User = get_user_model()
        self.user = User.objects.create_user('testuser', 'test@testing.com', 'password')
        self.client.login(username='testuser', password='password')

    def doPost(self, url, data={}):
        response = self.client.post(url, data=data, format='json')

        return response


class StockLocationTest(StockAPITestCase):
    """
    Series of API tests for the StockLocation API
    """
    list_url = reverse('api-location-list')

    def setUp(self):
        super().setUp()

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


class StockItemTest(StockAPITestCase):
    """
    Series of API tests for the StockItem API
    """

    list_url = reverse('api-stock-list')

    def detail_url(self, pk):
        return reverse('api-stock-detail', kwargs={'pk': pk})

    def setUp(self):
        super().setUp()
        # Create some stock locations
        top = StockLocation.objects.create(name='A', description='top')

        StockLocation.objects.create(name='B', description='location b', parent=top)
        StockLocation.objects.create(name='C', description='location c', parent=top)

    def test_get_stock_list(self):
        response = self.client.get(self.list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stock_item_create(self):
        """
        Test creation of a StockItem via the API
        """

        # POST with an empty part reference

        response = self.client.post(
            self.list_url,
            data={
                'quantity': 10,
                'location': 1
            }
        )

        self.assertContains(response, 'This field is required', status_code=status.HTTP_400_BAD_REQUEST)
        
        # POST with an invalid part reference

        response = self.client.post(
            self.list_url,
            data={
                'quantity': 10,
                'location': 1,
                'part': 10000000,
            }
        )

        self.assertContains(response, 'does not exist', status_code=status.HTTP_400_BAD_REQUEST)

        # POST without quantity
        response = self.client.post(
            self.list_url,
            data={
                'part': 1,
                'location': 1,
            }
        )

        self.assertContains(response, 'This field is required', status_code=status.HTTP_400_BAD_REQUEST)

        # POST with quantity and part and location
        response = self.client.post(
            self.list_url,
            data={
                'part': 1,
                'location': 1,
                'quantity': 10,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class StocktakeTest(StockAPITestCase):
    """
    Series of tests for the Stocktake API
    """

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

    def test_transfer(self):
        """
        Test stock transfers
        """

        data = {
            'item': {
                'pk': 1234,
                'quantity': 10,
            },
            'location': 1,
            'notes': "Moving to a new location"
        }

        url = reverse('api-stock-transfer')

        response = self.doPost(url, data)
        self.assertContains(response, "Moved 1 parts to", status_code=status.HTTP_200_OK)

        # Now try one which will fail due to a bad location
        data['location'] = 'not a location'

        response = self.doPost(url, data)
        self.assertContains(response, 'Valid location must be specified', status_code=status.HTTP_400_BAD_REQUEST)


class StockTestResultTest(StockAPITestCase):

    def get_url(self):
        return reverse('api-stock-test-result-list')

    def test_list(self):

        url = self.get_url()
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 4)

        response = self.client.get(url, data={'stock_item': 105})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 4)

    def test_post_fail(self):
        # Attempt to post a new test result without specifying required data

        url = self.get_url()

        response = self.client.post(
            url,
            data={
                'test': 'A test',
                'result': True,
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # This one should pass!
        response = self.client.post(
            url,
            data={
                'test': 'A test',
                'stock_item': 105,
                'result': True,
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post(self):
        # Test creation of a new test result

        url = self.get_url()

        response = self.client.get(url)
        n = len(response.data)

        data = {
            'stock_item': 105,
            'test': 'Checked Steam Valve',
            'result': False,
            'value': '150kPa',
            'notes': 'I guess there was just too much pressure?',
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(url)
        self.assertEqual(len(response.data), n + 1)

        # And read out again
        response = self.client.get(url, data={'test': 'Checked Steam Valve'})

        self.assertEqual(len(response.data), 1)

        test = response.data[0]
        self.assertEqual(test['value'], '150kPa')
        self.assertEqual(test['user'], self.user.pk)
