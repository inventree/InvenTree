""" Low level tests for the InvenTree API """

from rest_framework.test import APITestCase
from rest_framework import status

from django.urls import reverse
from django.contrib.auth import get_user_model

from base64 import b64encode


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

    token = None

    def setUp(self):

        # Create a user (but do not log in!)
        get_user_model().objects.create_user(self.username, 'user@email.com', self.password)

    def basicAuth(self):
        # Use basic authentication

        authstring = bytes("{u}:{p}".format(u=self.username, p=self.password), "ascii")

        # Use "basic" auth by default
        auth = b64encode(authstring).decode("ascii")
        self.client.credentials(HTTP_AUTHORIZATION="Basic {auth}".format(auth=auth))

    def tokenAuth(self):

        self.basicAuth()
        token_url = reverse('api-token')
        response = self.client.get(token_url, format='json', data={})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

        token = response.data['token']
        self.token = token

    def token_failure(self):
        # Test token endpoint without basic auth
        url = reverse('api-token')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIsNone(self.token)

    def token_success(self):

        self.tokenAuth()
        self.assertIsNotNone(self.token)

    def test_info_view(self):
        """
        Test that we can read the 'info-view' endpoint.
        """

        url = reverse('api-inventree-info')

        response = self.client.get(url, format='json')

        data = response.json()
        self.assertIn('server', data)
        self.assertIn('version', data)
        self.assertIn('instance', data)

        self.assertEquals('InvenTree', data['server'])
