""" Unit tests for action plugins """

from django.test import TestCase
from django.contrib.auth import get_user_model


class SampleIntegrationPluginTests(TestCase):
    """ Tests for SampleIntegrationPlugin """

    def setUp(self):
        # Create a user for auth
        user = get_user_model()
        user.objects.create_user('testuser', 'test@testing.com', 'password')

        self.client.login(username='testuser', password='password')

    def test_view(self):
        """check the function of the custom  sample plugin """
        response = self.client.get('/plugin/sample/ho/he/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'Hi there testuser this works')
