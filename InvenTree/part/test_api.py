from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Part, PartCategory
from .models import BomItem


class PartAPITest(APITestCase):
    """
    Series of tests for the Part DRF API
    - Tests for Part API
    - Tests for PartCategory API
    """

    def setUp(self):
        # Create a user for auth
        User = get_user_model()
        User.objects.create_user('testuser', 'test@testing.com', 'password')

        self.client.login(username='testuser', password='password')
        
        # Create some test data
        TOP = PartCategory.objects.create(name='Top', description='Top level category')
        
        A = PartCategory.objects.create(name='A', description='Cat A', parent=TOP)
        B = PartCategory.objects.create(name='B', description='Cat B', parent=TOP)
        C = PartCategory.objects.create(name='C', description='Cat C', parent=TOP)

        Part.objects.create(name='Top.t', description='t in TOP', category=TOP)

        Part.objects.create(name='A.a', description='a in A', category=A)
        Part.objects.create(name='B.b', description='b in B', category=B)
        Part.objects.create(name='C.c1', description='c1 in C', category=C)
        Part.objects.create(name='C.c2', description='c2 in C', category=C)

    def test_get_categories(self):
        # Test that we can retrieve list of part categories
        url = reverse('api-part-category-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_add_categories(self):
        # Check that we can add categories
        data = {
            'name': 'Animals',
            'description': 'All animals go here'
        }

        url = reverse('api-part-category-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['pk'], 5)

        # Add some sub-categories to the top-level 'Animals' category
        for animal in ['cat', 'dog', 'zebra']:
            data = {
                'name': animal,
                'description': 'A sort of animal',
                'parent': 5,
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['parent'], 5)
            self.assertEqual(response.data['name'], animal)
            self.assertEqual(response.data['pathstring'], 'Animals/' + animal)

        # There should be now 8 categories
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 8)

    def test_cat_detail(self):
        url = reverse('api-part-category-detail', kwargs={'pk': 4})
        response = self.client.get(url, format='json')

        # Test that we have retrieved the category
        self.assertEqual(response.data['description'], 'Cat C')
        self.assertEqual(response.data['parent'], 1)

        # Change some data and post it back
        data = response.data
        data['name'] = 'Changing category'
        data['parent'] = None
        data['description'] = 'Changing the description'
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Changing the description')

    def test_get_all_parts(self):
        url = reverse('api-part-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_get_parts_by_cat(self):
        url = reverse('api-part-list')
        data = {'category': 4}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # There should only be 2 objects in category C
        self.assertEqual(len(response.data), 2)

        for part in response.data:
            self.assertEqual(part['category'], 4)

    def test_include_children(self):
        """ Test the special 'include_child_categories' flag
        If provided, parts are provided for ANY child category (recursive)
        """
        url = reverse('api-part-list')
        data = {'category': 1}

        response = self.client.get(url, data, format='json')

        # There should be 1 part in this category
        self.assertEqual(len(response.data), 1)

        data['include_child_categories'] = 1

        # Now request to include child categories
        response = self.client.get(url, data, format='json')

        # Now there should be 5 total parts
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)


class BomAPITest(APITestCase):

    def setUp(self):
        # Create a user for auth
        User = get_user_model()
        User.objects.create_user('testuser', 'test@testing.com', 'password')

        self.client.login(username='testuser', password='password')

        # Create some parts
        m1 = Part.objects.create(name='A thing', description='Made from other parts', buildable=True)
        m2 = Part.objects.create(name='Another thing', description='Made from other parts', buildable=True)
        
        s1 = Part.objects.create(name='Sub 1', description='Required to make a thing')
        s2 = Part.objects.create(name='Sub 2', description='Required to make a thing')
        s3 = Part.objects.create(name='Sub 3', description='Required to make a thing')

        # Link BOM items together
        BomItem.objects.create(part=m1, sub_part=s1, quantity=10)
        BomItem.objects.create(part=m1, sub_part=s2, quantity=100)
        BomItem.objects.create(part=m1, sub_part=s3, quantity=40)

        BomItem.objects.create(part=m2, sub_part=s3, quantity=7)

    def test_get_bom_list(self):
        # There should be 4 BomItem objects in the database
        url = reverse('api-bom-list')
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 4)

    def test_get_bom_detail(self):
        # Get the detail for a single BomItem
        url = reverse('api-bom-detail', kwargs={'pk': 3})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 40)

        # Increase the quantity
        data = response.data
        data['quantity'] = 57
        data['note'] = 'Added a note'

        response = self.client.patch(url, data, format='json')

        # Check that the quantity was increased and a note added
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 57)
        self.assertEqual(response.data['note'], 'Added a note')

    def test_add_bom_item(self):
        url = reverse('api-bom-list')

        data = {
            'part': 2,
            'sub_part': 4,
            'quantity': 777,
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Now try to create a BomItem which points to a non-buildable part (should fail)
        data['part'] = 3
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Now try to create a BomItem which references itself
        data['part'] = 2
        data['sub_part'] = 2
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot be added to its own', str(response.data['sub_part'][0]))
