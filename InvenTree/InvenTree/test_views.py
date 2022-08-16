"""Unit tests for the main web views."""

import os

from django.contrib.auth import get_user_model
from django.urls import reverse

from InvenTree.helpers import InvenTreeTestCase


class ViewTests(InvenTreeTestCase):
    """Tests for various top-level views."""

    username = 'test_user'
    password = 'test_pass'

    def test_api_doc(self):
        """Test that the api-doc view works."""
        api_url = os.path.join(reverse('index'), 'api-doc') + '/'

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

    def test_index_redirect(self):
        """Top-level URL should redirect to "index" page."""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)

    def get_index_page(self):
        """Retrieve the index page (used for subsequent unit tests)"""
        response = self.client.get("/index/")

        self.assertEqual(response.status_code, 200)

        return str(response.content.decode())

    def test_panels(self):
        """Test that the required 'panels' are present."""
        content = self.get_index_page()

        self.assertIn("<div id='detail-panels'>", content)

        # TODO: In future, run the javascript and ensure that the panels get created!

    def test_settings_page(self):
        """Test that the 'settings' page loads correctly"""

        # Settings page loads
        url = reverse('settings')

        # Attempt without login
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Login with default client
        self.client.login(username=self.username, password=self.password)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        user_panels = [
            'account',
            'user-display',
            'user-home',
            'user-reports',
        ]

        staff_panels = [
            'server',
            'login',
            'barcodes',
            'currencies',
            'parts',
            'stock',
        ]

        plugin_panels = [
            'plugin',
        ]

        # Default user has staff access, so all panels will be present
        for panel in user_panels + staff_panels + plugin_panels:
            self.assertIn(f"select-{panel}", content)
            self.assertIn(f"panel-{panel}", content)

        # Now create a user who does not have staff access
        pleb_user = get_user_model().objects.create_user(
            username='pleb',
            password='notstaff',
        )

        pleb_user.groups.add(self.group)
        pleb_user.is_superuser = False
        pleb_user.is_staff = False
        pleb_user.save()

        self.client.logout()

        result = self.client.login(
            username='pleb',
            password='notstaff',
        )

        self.assertTrue(result)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        # Normal user still has access to user-specific panels
        for panel in user_panels:
            self.assertIn(f"select-{panel}", content)
            self.assertIn(f"panel-{panel}", content)

        # Normal user does NOT have access to global or plugin settings
        for panel in staff_panels + plugin_panels:
            self.assertNotIn(f"select-{panel}", content)
            self.assertNotIn(f"panel-{panel}", content)

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
