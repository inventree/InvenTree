""" Unit tests for plugins """

from django.test import TestCase

import plugins.plugin

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

