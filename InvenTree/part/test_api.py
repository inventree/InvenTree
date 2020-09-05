from rest_framework.test import APITestCase
from rest_framework import status

from django.urls import reverse
from django.contrib.auth import get_user_model

from part.models import Part
from stock.models import StockItem
from company.models import Company

from InvenTree.status_codes import StockStatus


class PartAPITest(APITestCase):
    """
    Series of tests for the Part DRF API
    - Tests for Part API
    - Tests for PartCategory API
    """

    fixtures = [
        'category',
        'part',
        'location',
        'bom',
        'test_templates',
    ]

    def setUp(self):
        # Create a user for auth
        User = get_user_model()
        User.objects.create_user('testuser', 'test@testing.com', 'password')

        self.client.login(username='testuser', password='password')

    def test_get_categories(self):
        """ Test that we can retrieve list of part categories """
        url = reverse('api-part-category-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 8)

    def test_add_categories(self):
        """ Check that we can add categories """
        data = {
            'name': 'Animals',
            'description': 'All animals go here'
        }

        url = reverse('api-part-category-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        parent = response.data['pk']

        # Add some sub-categories to the top-level 'Animals' category
        for animal in ['cat', 'dog', 'zebra']:
            data = {
                'name': animal,
                'description': 'A sort of animal',
                'parent': parent,
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['parent'], parent)
            self.assertEqual(response.data['name'], animal)
            self.assertEqual(response.data['pathstring'], 'Animals/' + animal)

        # There should be now 8 categories
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 12)

    def test_cat_detail(self):
        url = reverse('api-part-category-detail', kwargs={'pk': 4})
        response = self.client.get(url, format='json')

        # Test that we have retrieved the category
        self.assertEqual(response.data['description'], 'Integrated Circuits')
        self.assertEqual(response.data['parent'], 1)

        # Change some data and post it back
        data = response.data
        data['name'] = 'Changing category'
        data['parent'] = None
        data['description'] = 'Changing the description'
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Changing the description')
        self.assertIsNone(response.data['parent'])

    def test_get_all_parts(self):
        url = reverse('api-part-list')
        data = {'cascade': True}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 13)

    def test_get_parts_by_cat(self):
        url = reverse('api-part-list')
        data = {'category': 2}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # There should only be 2 objects in category C
        self.assertEqual(len(response.data), 2)

        for part in response.data:
            self.assertEqual(part['category'], 2)

    def test_include_children(self):
        """ Test the special 'include_child_categories' flag
        If provided, parts are provided for ANY child category (recursive)
        """
        url = reverse('api-part-list')
        data = {'category': 1, 'cascade': True}

        # Now request to include child categories
        response = self.client.get(url, data, format='json')

        # Now there should be 5 total parts
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_get_bom_list(self):
        """ There should be 4 BomItem objects in the database """
        url = reverse('api-bom-list')
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 4)

    def test_get_bom_detail(self):
        # Get the detail for a single BomItem
        url = reverse('api-bom-item-detail', kwargs={'pk': 3})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(int(float(response.data['quantity'])), 25)

        # Increase the quantity
        data = response.data
        data['quantity'] = 57
        data['note'] = 'Added a note'

        response = self.client.patch(url, data, format='json')

        # Check that the quantity was increased and a note added
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(int(float(response.data['quantity'])), 57)
        self.assertEqual(response.data['note'], 'Added a note')

    def test_add_bom_item(self):
        url = reverse('api-bom-list')

        data = {
            'part': 100,
            'sub_part': 4,
            'quantity': 777,
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Now try to create a BomItem which points to a non-assembly part (should fail)
        data['part'] = 3
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # TODO - Now try to create a BomItem which references itself
        data['part'] = 2
        data['sub_part'] = 2
        response = self.client.post(url, data, format='json')

    def test_test_templates(self):

        url = reverse('api-part-test-template-list')

        # List ALL items
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 7)

        # Request for a particular part
        response = self.client.get(url, data={'part': 10000})
        self.assertEqual(len(response.data), 5)

        response = self.client.get(url, data={'part': 10004})
        self.assertEqual(len(response.data), 7)

        # Try to post a new object (should succeed)
        response = self.client.post(
            url,
            data={
                'part': 10000,
                'test_name': 'New Test',
                'required': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Try to post a new test with the same name (should fail)
        response = self.client.post(
            url,
            data={
                'part': 10004,
                'test_name': "   newtest"
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try to post a new test against a non-trackable part (should fail)
        response = self.client.post(
            url,
            data={
                'part': 1,
                'test_name': 'A simple test',
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PartAPIAggregationTest(APITestCase):
    """
    Tests to ensure that the various aggregation annotations are working correctly...
    """

    fixtures = [
        'category',
        'company',
        'part',
        'location',
        'bom',
        'test_templates',
    ]

    def setUp(self):
        # Create a user for auth
        User = get_user_model()
        User.objects.create_user('testuser', 'test@testing.com', 'password')

        self.client.login(username='testuser', password='password')

        # Add a new part
        self.part = Part.objects.create(
            name='Banana',
        )

        # Create some stock items associated with the part

        # First create 600 units which are OK
        StockItem.objects.create(part=self.part, quantity=100)
        StockItem.objects.create(part=self.part, quantity=200)
        StockItem.objects.create(part=self.part, quantity=300)

        # Now create another 400 units which are LOST
        StockItem.objects.create(part=self.part, quantity=400, status=StockStatus.LOST)

    def get_part_data(self):
        url = reverse('api-part-list')

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for part in response.data:
            if part['pk'] == self.part.pk:
                return part

        # We should never get here!
        self.assertTrue(False)

    def test_stock_quantity(self):
        """
        Simple test for the stock quantity
        """

        data = self.get_part_data()

        self.assertEqual(data['in_stock'], 600)
        self.assertEqual(data['stock_item_count'], 4)
    
        # Add some more stock items!!
        for i in range(100):
            StockItem.objects.create(part=self.part, quantity=5)

        # Add another stock item which is assigned to a customer (and shouldn't count)
        customer = Company.objects.get(pk=4)
        StockItem.objects.create(part=self.part, quantity=9999, customer=customer)

        data = self.get_part_data()

        self.assertEqual(data['in_stock'], 1100)
        self.assertEqual(data['stock_item_count'], 105)
