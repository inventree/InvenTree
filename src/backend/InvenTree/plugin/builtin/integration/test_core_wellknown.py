"""Test for built-in InvenTree well-known plugin."""

from django.test import override_settings
from django.urls import reverse

from common.models import InvenTreeSetting
from InvenTree.unit_test import InvenTreeAPITestCase
from plugin.registry import registry


class InvenTreeWellKnownTest(InvenTreeAPITestCase):
    """Tests for the InvenTreeWellKnown plugin."""

    def setUp(self):
        """Setup some testing drivers/machines."""
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_URL', True, None)
        registry.reload_plugins()

    @override_settings(
        SITE_URL='http://testserver', CSRF_TRUSTED_ORIGINS=['http://testserver']
    )
    def test_well_known_urls(self):
        """Test that the well-known URLs are returned correctly from the index view."""
        url = reverse('well-known:index')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('well_known_urls', data)

        # passkey URLs should be present
        self.assertIn('passkey-endpoints', data['well_known_urls'])

    @override_settings(
        SITE_URL='http://testserver', CSRF_TRUSTED_ORIGINS=['http://testserver']
    )
    def test_passkey_view(self):
        """Test that the passkey view returns the correct JSON response."""
        response = self.client.get(
            '/.well-known/passkey-endpoints/', follow=True, accept='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('enroll', data)
        self.assertIn('manage', data)
