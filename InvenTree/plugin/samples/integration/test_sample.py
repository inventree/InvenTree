"""Unit tests for action plugins."""

from django.core.exceptions import ValidationError

from InvenTree.unit_test import InvenTreeTestCase
from plugin import registry


class SampleIntegrationPluginTests(InvenTreeTestCase):
    """Tests for SampleIntegrationPlugin."""

    def test_view(self):
        """Check the function of the custom  sample plugin."""
        response = self.client.get('/plugin/sample/ho/he/')
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
