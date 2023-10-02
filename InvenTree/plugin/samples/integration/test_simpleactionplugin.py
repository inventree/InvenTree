"""Unit tests for action plugins."""

from InvenTree.unit_test import InvenTreeTestCase
from plugin.samples.integration.simpleactionplugin import SimpleActionPlugin


class SimpleActionPluginTests(InvenTreeTestCase):
    """Tests for SampleIntegrationPlugin."""

    def setUp(self):
        """Setup for tests."""
        super().setUp()

    def test_name(self):
        """Check plugin names."""

        self.plugin = SimpleActionPlugin()
        self.assertEqual(self.plugin.plugin_name(), "SimpleActionPlugin")
        self.assertEqual(self.plugin.action_name(), "simple")
        self.assertEqual(self.plugin.slug, "simpleaction")

    def test_function(self):
        """Check if functions work."""

        # Ensure the plugin is activated
        from plugin.registry import registry

        registry.set_plugin_state('simpleaction', True)

        # test functions
        response = self.client.post('/api/action/', data={'action': "simple", 'data': {'foo': "bar", }})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {
                "action": 'simple',
                "result": True,
                "info": {
                    "user": self.username,
                    "hello": "world",
                },
            }
        )

        # test again with the plugin disabled
        registry.set_plugin_state('simpleaction', False)

        response = self.client.post('/api/action/', data={'action': "simple", 'data': {'foo': "bar", }})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('action', response.data)
