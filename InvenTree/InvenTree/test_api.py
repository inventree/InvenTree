""" Low level tests for the InvenTree API """

from rest_framework.test import APITestCase
from rest_framework import status

from django.urls import reverse

from django.contrib.auth import get_user_model


class APITests(APITestCase):
    """ Tests for the InvenTree API """

    fixtures = [
        'location',
        'stock',
        'part',
        'category',
    ]

    username = 'test_user'
    password = 'test_pass'

    def setUp(self):

        # Create a user (but do not log in!)
        User = get_user_model()
        User.objects.create_user(self.username, 'user@email.com', self.password)

    def test_get_token_fail(self):
        """ Ensure that an invalid user cannot get a token """

        token_url = reverse('api-token')

        response = self.client.post(token_url, format='json', data={'username': 'bad', 'password': 'also_bad'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse('token' in response.data)

    def test_get_token_pass(self):
        """ Ensure that a valid user can request an API token """

        token_url = reverse('api-token')

        # POST to retreive a token
        response = self.client.post(token_url, format='json', data={'username': self.username, 'password': self.password})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.data)
        self.assertTrue('pk' in response.data)
        self.assertTrue(len(response.data['token']) > 0)

        # Now, use the token to access other data
        token = response.data['token']

        part_url = reverse('api-part-list')

        # Try to access without a token
        response = self.client.get(part_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Now, with the token
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(part_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
