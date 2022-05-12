"""Tests for middleware functions"""

from django.test import TestCase

from django.contrib.auth import get_user_model
from django.urls import reverse


class MiddlewareTests(TestCase):
    """Test for middleware functions"""

    def check_path(self, url, code=200, **kwargs):
        response = self.client.get(url, HTTP_ACCEPT='application/json', **kwargs)
        self.assertEqual(response.status_code, code)
        return response

    def setUp(self):
        super().setUp()

        # Create a user
        user = get_user_model()

        self.user = user.objects.create_user(username='username', email='user@email.com', password='password')
        self.client.login(username='username', password='password')

    def test_AuthRequiredMiddleware(self):
        """Test the auth middleware"""

        # test that /api/ routes go through
        self.check_path(reverse('api-inventree-info'))

        # logout
        self.client.logout()

        # check that static files go through
        self.check_path('/static/admin/fonts/LICENSE.txt')

        # check that account things go through
        self.check_path(reverse('account_login'))

        # logout goes diretly to login
        self.check_path(reverse('account_logout'))

        # check that frontend code is redirected to login
        response = self.check_path(reverse('stats'), 302)
        self.assertEqual(response.url, '/accounts/login/?next=/stats/')

        # check that a 401 is raised
        self.check_path(reverse('settings.js'), 401)
