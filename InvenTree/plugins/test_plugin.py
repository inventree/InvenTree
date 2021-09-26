""" Unit tests for plugins """

from django.test import TestCase

import plugins.plugin
from plugins.plugins import load_integration_plugins  # , load_action_plugins, load_barcode_plugins


class InvenTreePluginTests(TestCase):
    """ Tests for InvenTreePlugin """
    def setUp(self):
        self.plugin = plugins.plugin.InvenTreePlugin()

        class NamedPlugin(plugins.plugin.InvenTreePlugin):
            """a named plugin"""
            PLUGIN_NAME = 'abc123'

        self.named_plugin = NamedPlugin()

    def test_basic_plugin_init(self):
        """check if a basic plugin intis"""
        self.assertEqual(self.plugin.PLUGIN_NAME, '')
        self.assertEqual(self.plugin.plugin_name(), '')

    def test_basic_plugin_name(self):
        """check if the name of a basic plugin can be set"""
        self.assertEqual(self.named_plugin.PLUGIN_NAME, 'abc123')
        self.assertEqual(self.named_plugin.plugin_name(), 'abc123')


class PluginIntegrationTests(TestCase):
    """ Tests for general plugin functions """

    def test_plugin_loading(self):
        """check if plugins load as expected"""
        plugin_names_integration = [a().plugin_name() for a in load_integration_plugins()]
        # plugin_names_barcode = [a().plugin_name() for a in load_barcode_plugins()]  # TODO refactor barcode plugin to support standard loading
        # plugin_names_action = [a().plugin_name() for a in load_action_plugins()]  # TODO refactor action plugin to support standard loading

        self.assertEqual(plugin_names_integration, ['NoIntegrationPlugin', 'WrongIntegrationPlugin', 'SampleIntegrationPlugin'])
        # self.assertEqual(plugin_names_action, '')
        # self.assertEqual(plugin_names_barcode, '')
