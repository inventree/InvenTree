""" Unit tests for the main web views """

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

import os


class ViewTests(TestCase):
    """ Tests for various top-level views """

    username = 'test_user'
    password = 'test_pass'

    def setUp(self):

        # Create a user
        get_user_model().objects.create_user(self.username, 'user@email.com', self.password)

        self.client.login(username=self.username, password=self.password)

    def test_api_doc(self):
        """ Test that the api-doc view works """

        api_url = os.path.join(reverse('index'), 'api-doc') + '/'

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
