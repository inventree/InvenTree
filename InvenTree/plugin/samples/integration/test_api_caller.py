"""Unit tests for action caller sample."""

from django.test import TestCase

from plugin import registry


class SampleApiCallerPluginTests(TestCase):
    """Tests for SampleApiCallerPluginTests."""

    def setUp(self):
        """Setup for SampleApiCallerPluginTests."""
        super().setUp()

        # Ensure the plugin is installed
        registry.set_plugin_state('sample-api-caller', True)

    def test_return(self):
        """Check if the external API call works."""
        # The plugin should be defined
        self.assertIn('sample-api-caller', registry.plugins)
        plg = registry.plugins['sample-api-caller']
        self.assertTrue(plg)

        # Perform an API call
        result = plg.get_external_url()
        self.assertTrue(result)
        self.assertIn('data', result)
