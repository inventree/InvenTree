"""Unit tests for action plugins."""

from InvenTree.unit_test import InvenTreeTestCase
from plugin.registry import registry
from plugin.samples.integration.simpleactionplugin import SimpleActionPlugin


class SimpleActionPluginTests(InvenTreeTestCase):
    """Tests for SampleIntegrationPlugin."""

    def test_name(self):
        """Check plugn names."""
        plg = SimpleActionPlugin()
        self.assertEqual(plg.plugin_name(), 'SimpleActionPlugin')
        self.assertEqual(plg.action_name(), 'simple')

    def set_plugin_state(self, state: bool):
        """Set the enabled state of the SimpleActionPlugin."""
        cfg = registry.get_plugin_config('simpleaction')
        cfg.active = state
        cfg.save()

    def test_function(self):
        """Check if functions work."""
        data = {'action': 'simple', 'data': {'foo': 'bar'}}

        self.set_plugin_state(False)

        response = self.client.post('/api/action/', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.data)

        # Now enable the plugin
        self.set_plugin_state(True)

        # test functions
        response = self.client.post('/api/action/', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {
                'action': 'simple',
                'result': True,
                'info': {'user': self.username, 'hello': 'world'},
            },
        )
