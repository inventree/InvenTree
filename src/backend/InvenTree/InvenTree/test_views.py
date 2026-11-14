"""Unit tests for the main web views."""

import os

from django.test import override_settings
from django.urls import reverse

from InvenTree.unit_test import InvenTreeTestCase


class ViewTests(InvenTreeTestCase):
    """Tests for various top-level views."""

    username = 'test_user'
    password = 'test_pass'

    @override_settings(
        SITE_URL='http://testserver', CSRF_TRUSTED_ORIGINS=['http://testserver']
    )
    def test_api_doc(self):
        """Test that the api-doc view works."""
        api_url = os.path.join(reverse('index'), 'api-doc') + '/'

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

    @override_settings(
        SITE_URL='http://testserver', CSRF_TRUSTED_ORIGINS=['http://testserver']
    )
    def test_index_redirect(self):
        """Top-level URL should redirect to "index" page."""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 302)

    def get_index_page(self):
        """Retrieve the index page (used for subsequent unit tests)."""
        response = self.client.get('/index/')

        self.assertEqual(response.status_code, 200)

        return str(response.content.decode())

    def test_url_login(self):
        """Test logging in via arguments."""
        # Log out
        self.client.logout()
        response = self.client.get('/index/')
        self.assertEqual(response.status_code, 302)

        # Try login with url
        response = self.client.get(
            f'/accounts/login/?next=/&login={self.username}&password={self.password}'
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/web/logged-in/?next=%2F')

    def test_account_login_redirect(self):
        """Test that the login redirect preserves the 'next' parameter."""
        self.client.logout()

        # AuthRequiredMiddleware -> /accounts/login/?next=<requested path>
        response = self.client.get('/part/42/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=/part/42/')

        # -> SPA /logged-in, with the target (and any query string) kept
        response = self.client.get(response.url)
        self.assertEqual(response.url, '/web/logged-in/?next=%2Fpart%2F42%2F')

        response = self.client.get('/accounts/login/?next=/part/42/?search=abc')
        self.assertEqual(
            response.url, '/web/logged-in/?next=%2Fpart%2F42%2F%3Fsearch%3Dabc'
        )

        # Old build order links are remapped to their SPA route
        for legacy in ['/build/42/', '/build/42']:
            response = self.client.get(f'/accounts/login/?next={legacy}')
            self.assertEqual(
                response.url,
                '/web/logged-in/?next=%2Fmanufacturing%2Fbuild-order%2F42%2F',
                f'next={legacy} was not remapped',
            )

        # Absolute URLs must not be forwarded (open redirect prevention);
        # fall back to the plain frontend redirect
        for unsafe in [
            'https://example.org/evil/',
            '//example.org/evil/',
            'http://example.org/evil/',
        ]:
            response = self.client.get(f'/accounts/login/?next={unsafe}')
            self.assertEqual(response.url, '/web', f'next={unsafe} must not be kept')

        # No next parameter at all
        response = self.client.get(reverse('account_login'))
        self.assertEqual(response.url, '/web')
