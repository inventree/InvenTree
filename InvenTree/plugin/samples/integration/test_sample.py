"""Unit tests for action plugins."""

from django.core.exceptions import ValidationError

from InvenTree.unit_test import InvenTreeTestCase
from plugin import registry


class SampleIntegrationPluginTests(InvenTreeTestCase):
    """Tests for SampleIntegrationPlugin."""

    def test_view(self):
        """Check the function of the custom  sample plugin."""
        from common.models import InvenTreeSetting

        url = '/plugin/sample/ho/he/'

        # First, check with custom URLs disabled
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_URL', False, None)

        # Requires a full reload of the registry
        registry.reload_plugins()

        # URL should redirect to index page
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Now, check with custom URLs enabled
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_URL', True, None)

        # Requires a full reload of the registry
        registry.reload_plugins()

        # And ensure that the plugin is enabled
        registry.set_plugin_state('sample', True)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content, b'Hi there testuser this works')

    def test_settings(self):
        """Check the SettingsMixin.check_settings function."""
        plugin = registry.get_plugin('sample')
        self.assertIsNotNone(plugin)

        # check settings
        self.assertEqual(plugin.check_settings(), (False, ['API_KEY']))
        plugin.set_setting('API_KEY', "dsfiodsfjsfdjsf")
        self.assertEqual(plugin.check_settings(), (True, []))

        # validator

    def test_settings_validator(self):
        """Test settings validator for plugins."""
        plugin = registry.get_plugin('sample')
        valid_json = '{"ts": 13}'
        not_valid_json = '{"ts""13"}'

        # no error, should pass validator
        plugin.set_setting('VALIDATOR_SETTING', valid_json)

        # should throw an error
        with self.assertRaises(ValidationError):
            plugin.set_setting('VALIDATOR_SETTING', not_valid_json)
