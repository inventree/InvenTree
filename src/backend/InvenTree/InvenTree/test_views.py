"""Unit tests for the main web views."""

import os
import re

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
        """Test that the api-doc view renders a usable Redoc page.

        A 200 response alone is not sufficient - the page is a thin HTML shell
        which loads Redoc from a CDN and points it at the schema endpoint.
        Ref: https://github.com/inventree/InvenTree/issues/13200
        """
        api_url = os.path.join(reverse('index'), 'api-doc') + '/'

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        html = response.content.decode()
        schema_url = reverse('schema')

        # The page must point Redoc at our schema endpoint
        self.assertIn(schema_url, html)

        # Find the Redoc bundle which is loaded by the page
        scripts = re.findall(r'<script([^>]*)\ssrc="([^"]+)"', html)
        redoc_scripts = [(attrs, src) for attrs, src in scripts if 'redoc' in src]
        self.assertEqual(len(redoc_scripts), 1, 'Redoc script not found in api-doc')

        attrs, src = redoc_scripts[0]

        # The Redoc version must be pinned - '@latest' can (and did) change under us
        match = re.search(r'redoc@(\d+)(?:\.\d+)*/', src)
        self.assertIsNotNone(
            match, f'Redoc distribution must be pinned to a version: {src}'
        )

        # Redoc >= 3 is ES-module only and cannot be loaded via a classic <script>
        if int(match.group(1)) >= 3:
            self.assertIn(
                'type="module"',
                attrs,
                f'Redoc {match.group(1)}.x must be loaded as an ES module: {src}',
            )

        # The schema which Redoc loads must contain generated API data
        response = self.client.get(schema_url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        schema = response.json()
        self.assertTrue(schema['openapi'].startswith('3.'))
        self.assertEqual(schema['info']['title'], 'InvenTree API')
        self.assertIn('/api/part/', schema['paths'])
        self.assertIn('/api/stock/', schema['paths'])
        self.assertGreater(len(schema['paths']), 100)

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
        self.assertEqual(response.url, '/web')
