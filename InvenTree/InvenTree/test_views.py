""" Unit tests for the main web views """

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

import os


class ViewTests(TestCase):
    """ Tests for various top-level views """

    def setUp(self):

        # Create a user
        User = get_user_model()
        User.objects.create_user('username', 'user@email.com', 'password')

        self.client.login(username='username', password='password')

    def test_api_doc(self):
        """ Test that the api-doc view works """

        api_url = os.path.join(reverse('index'), 'api-doc') + '/'

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
