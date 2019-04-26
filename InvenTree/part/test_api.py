from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Part, PartCategory


class BomAPITest(APITestCase):

    def setUp(self):
        # Create a user for auth
        User = get_user_model()
        User.objects.create_user('testuser', 'test@testing.com', 'password')

        self.client.login(username='testuser', password='password')

    def test_category_list_empty(self):
        # Check that we can retrieve an (empty) category list
        url = reverse('api-part-category-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_add_categories(self):
        # Check that we can add categories
        data = {
            'name': 'Animals',
            'description': 'All animals go here'
        }

        url = reverse('api-part-category-list')
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['pk'], 1)

        # Add some sub-categories to the top-level 'Animals' category
        for animal in ['cat', 'dog', 'zebra']:
            data = {
                'name': animal,
                'description': 'A sort of animal',
                'parent': 1,
            }
            response = self.client.post(url, data=data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['parent'], 1)
            self.assertEqual(response.data['name'], animal)
            self.assertEqual(response.data['pathstring'], 'Animals/' + animal)

        # There should be now 4 categories
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 4)


class PartAPITest(APITestCase):

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

    def test_get_all_parts(self):
        url = reverse('api-part-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_get_parts_by_cat(self):
        url = reverse('api-part-list')
        data = {'category': 4}
        response = self.client.get(url, data=data, format='json')
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

        response = self.client.get(url, data=data, format='json')

        # There should be 1 part in this category
        self.assertEqual(len(response.data), 1)

        data['include_child_categories'] = 1

        # Now request to include child categories
        response = self.client.get(url, data=data, format='json')

        # Now there should be 5 total parts
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
