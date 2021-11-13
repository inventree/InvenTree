""" Unit tests for plugins """

from django.test import TestCase
from django.conf import settings

import plugin.plugin
import plugin.integration
from plugin.samples.integration.sample import SampleIntegrationPlugin
from plugin.samples.integration.another_sample import WrongIntegrationPlugin, NoIntegrationPlugin
from plugin.plugins import load_integration_plugins  # , load_action_plugins, load_barcode_plugins
import plugin.templatetags.plugin_extras as plugin_tags


class InvenTreePluginTests(TestCase):
    """ Tests for InvenTreePlugin """
    def setUp(self):
        self.plugin = plugin.plugin.InvenTreePlugin()

        class NamedPlugin(plugin.plugin.InvenTreePlugin):
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

        self.assertListEqual(list(set(plugin_names_integration)), ['WrongIntegrationPlugin', 'NoIntegrationPlugin', 'SampleIntegrationPlugin'])
        # self.assertEqual(plugin_names_action, '')
        # self.assertEqual(plugin_names_barcode, '')


class PluginTagTests(TestCase):
    """ Tests for the plugin extras """

    def setUp(self):
        self.sample = SampleIntegrationPlugin()
        self.plugin_no = NoIntegrationPlugin()
        self.plugin_wrong = WrongIntegrationPlugin()

    def test_tag_plugin_list(self):
        """test that all plugins are listed"""
        self.assertEqual(plugin_tags.plugin_list(), settings.INTEGRATION_PLUGINS)

    def test_tag_plugin_settings(self):
        """check all plugins are listed"""
        self.assertEqual(plugin_tags.plugin_settings(self.sample), settings.INTEGRATION_PLUGIN_SETTING.get(self.sample))

    def test_tag_mixin_enabled(self):
        """check that mixin enabled functions work"""
        key = 'urls'
        # mixin enabled
        self.assertEqual(plugin_tags.mixin_enabled(self.sample, key), True)
        # mixin not enabled
        self.assertEqual(plugin_tags.mixin_enabled(self.plugin_wrong, key), False)
        # mxixn not existing
        self.assertEqual(plugin_tags.mixin_enabled(self.plugin_no, key), False)
