"""Tests for middleware functions."""

from django.urls import reverse

from InvenTree.helpers import InvenTreeTestCase


class MiddlewareTests(InvenTreeTestCase):
    """Test for middleware functions."""

    def check_path(self, url, code=200, **kwargs):
        response = self.client.get(url, HTTP_ACCEPT='application/json', **kwargs)
        self.assertEqual(response.status_code, code)
        return response

    def test_AuthRequiredMiddleware(self):
        """Test the auth middleware."""
        # test that /api/ routes go through
        self.check_path(reverse('api-inventree-info'))

        # logout
        self.client.logout()

        # check that static files go through
        # TODO @matmair reenable this check
        # self.check_path('/static/css/inventree.css', 302)

        # check that account things go through
        self.check_path(reverse('account_login'))

        # logout goes diretly to login
        self.check_path(reverse('account_logout'))

        # check that frontend code is redirected to login
        response = self.check_path(reverse('stats'), 302)
        self.assertEqual(response.url, '/accounts/login/?next=/stats/')

        # check that a 401 is raised
        self.check_path(reverse('settings.js'), 401)

    def test_token_auth(self):
        """Test auth with token auth."""
        # get token
        response = self.client.get(reverse('api-token'), format='json', data={})
        token = response.data['token']

        # logout
        self.client.logout()
        # this should raise a 401
        self.check_path(reverse('settings.js'), 401)

        # request with token
        self.check_path(reverse('settings.js'), HTTP_Authorization=f'Token {token}')

        # Request with broken token
        self.check_path(reverse('settings.js'), 401, HTTP_Authorization='Token abcd123')

        # should still fail without token
        self.check_path(reverse('settings.js'), 401)
