"""Unit tests for the main web views."""

import os

from InvenTree.helpers import InvenTreeTestCase


class ViewTests(InvenTreeTestCase):
    """Tests for various top-level views."""

    username = 'test_user'
    password = 'test_pass'

    def test_api_doc(self):
        """Test that the api-doc view works."""
        api_url = os.path.join('/api-doc') + '/'

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

    def test_index_redirect(self):
        """Top-level URL should redirect to "index" page."""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)

    def test_url_login(self):
        """Test logging in via arguments"""

        # Log out
        self.client.logout()
        response = self.client.get("/index/")
        self.assertEqual(response.status_code, 302)

        # Try login with url
        response = self.client.get(f"/accounts/login/?next=/&login={self.username}&password={self.password}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
