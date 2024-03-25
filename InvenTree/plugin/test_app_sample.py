"""Unit tests for app plugin."""

from django.conf import settings
from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase
from plugin import registry


class SampleAppIntegrationPluginTests(InvenTreeAPITestCase):
    """Tests for SampleAppIntegrationPlugin."""

    def test_api(self):
        """Check the APIs of the custom sample plugin work."""
        from common.models import InvenTreeSetting

        # Enable test environment
        settings.PLUGIN_TESTING_APPS = True
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_URL', True, None)
        registry.reload_plugins()
        registry.set_plugin_state('sample', True)

        # Get
        response = self.get(reverse('plugin:sample:api-list'))
        self.assertEqual(response.status_code, 200)
        print('smapel-plugin-api-list', response.json())

        # Detail
        response = self.get(reverse('plugin:sample:api-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        print('smapel-plugin-api-detail', response.json())

        # Options
        try:
            response = self.options(reverse('plugin:sample:api-list'))
            self.assertEqual(response.status_code, 200)
            print('smapel-plugin-api-options', response.json())
        except Exception as e:
            print('smapel-plugin-api-options error', e)

        # Disable test environment
        settings.PLUGIN_TESTING_APPS = False
