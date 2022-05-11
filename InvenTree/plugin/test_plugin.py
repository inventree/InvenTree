"""
Unit tests for plugins
"""

from datetime import datetime

from django.test import TestCase

from plugin.samples.integration.sample import SampleIntegrationPlugin
from plugin.samples.integration.another_sample import WrongIntegrationPlugin, NoIntegrationPlugin
import plugin.templatetags.plugin_extras as plugin_tags
from plugin import registry, InvenTreePlugin


class PluginTagTests(TestCase):
    """ Tests for the plugin extras """

    def setUp(self):
        self.sample = SampleIntegrationPlugin()
        self.plugin_no = NoIntegrationPlugin()
        self.plugin_wrong = WrongIntegrationPlugin()

    def test_tag_plugin_list(self):
        """test that all plugins are listed"""
        self.assertEqual(plugin_tags.plugin_list(), registry.plugins)

    def test_tag_incative_plugin_list(self):
        """test that all inactive plugins are listed"""
        self.assertEqual(plugin_tags.inactive_plugin_list(), registry.plugins_inactive)

    def test_tag_plugin_settings(self):
        """check all plugins are listed"""
        self.assertEqual(
            plugin_tags.plugin_settings(self.sample),
            registry.mixins_settings.get(self.sample)
        )

    def test_tag_mixin_enabled(self):
        """check that mixin enabled functions work"""
        key = 'urls'
        # mixin enabled
        self.assertEqual(plugin_tags.mixin_enabled(self.sample, key), True)
        # mixin not enabled
        self.assertEqual(plugin_tags.mixin_enabled(self.plugin_wrong, key), False)
        # mxixn not existing
        self.assertEqual(plugin_tags.mixin_enabled(self.plugin_no, key), False)

    def test_tag_safe_url(self):
        """test that the safe url tag works expected"""
        # right url
        self.assertEqual(plugin_tags.safe_url('api-plugin-install'), '/api/plugin/install/')
        # wrong url
        self.assertEqual(plugin_tags.safe_url('indexas'), None)

    def test_tag_plugin_errors(self):
        """test that all errors are listed"""
        self.assertEqual(plugin_tags.plugin_errors(), registry.errors)


class InvenTreePluginTests(TestCase):
    """ Tests for InvenTreePlugin """

    def setUp(self):
        self.plugin = InvenTreePlugin()

        class NamedPlugin(InvenTreePlugin):
            """a named plugin"""
            NAME = 'abc123'

        self.named_plugin = NamedPlugin()

        class SimpleInvenTreePlugin(InvenTreePlugin):
            NAME = 'SimplePlugin'

        self.plugin_simple = SimpleInvenTreePlugin()

        class OldInvenTreePlugin(InvenTreePlugin):
            PLUGIN_NAME = 'OldPlugin'

        self.plugin_old = OldInvenTreePlugin()

        class NameInvenTreePlugin(InvenTreePlugin):
            NAME = 'Aplugin'
            SLUG = 'a'
            TITLE = 'a titel'
            PUBLISH_DATE = "1111-11-11"
            AUTHOR = 'AA BB'
            DESCRIPTION = 'A description'
            VERSION = '1.2.3a'
            WEBSITE = 'http://aa.bb/cc'
            LICENSE = 'MIT'

        self.plugin_name = NameInvenTreePlugin()
        self.plugin_sample = SampleIntegrationPlugin()

    def test_basic_plugin_init(self):
        """check if a basic plugin intis"""
        self.assertEqual(self.plugin.NAME, '')
        self.assertEqual(self.plugin.plugin_name(), '')

    def test_basic_plugin_name(self):
        """check if the name of a basic plugin can be set"""
        self.assertEqual(self.named_plugin.NAME, 'abc123')
        self.assertEqual(self.named_plugin.plugin_name(), 'abc123')

    def test_basic_is_active(self):
        """check if a basic plugin is active"""
        self.assertEqual(self.plugin.is_active(), False)

    def test_action_name(self):
        """check the name definition possibilities"""
        # plugin_name
        self.assertEqual(self.plugin.plugin_name(), '')
        self.assertEqual(self.plugin_simple.plugin_name(), 'SimplePlugin')
        self.assertEqual(self.plugin_name.plugin_name(), 'Aplugin')

        # is_sampe
        self.assertEqual(self.plugin.is_sample, False)
        self.assertEqual(self.plugin_sample.is_sample, True)

        # slug
        self.assertEqual(self.plugin.slug, '')
        self.assertEqual(self.plugin_simple.slug, 'simpleplugin')
        self.assertEqual(self.plugin_name.slug, 'a')

        # human_name
        self.assertEqual(self.plugin.human_name, '')
        self.assertEqual(self.plugin_simple.human_name, 'SimplePlugin')
        self.assertEqual(self.plugin_name.human_name, 'a titel')

        # description
        self.assertEqual(self.plugin.description, '')
        self.assertEqual(self.plugin_simple.description, 'SimplePlugin')
        self.assertEqual(self.plugin_name.description, 'A description')

        # author
        self.assertEqual(self.plugin_name.author, 'AA BB')

        # pub_date
        self.assertEqual(self.plugin_name.pub_date, datetime(1111, 11, 11, 0, 0))

        # version
        self.assertEqual(self.plugin.version, None)
        self.assertEqual(self.plugin_simple.version, None)
        self.assertEqual(self.plugin_name.version, '1.2.3a')

        # website
        self.assertEqual(self.plugin.website, None)
        self.assertEqual(self.plugin_simple.website, None)
        self.assertEqual(self.plugin_name.website, 'http://aa.bb/cc')

        # license
        self.assertEqual(self.plugin.license, None)
        self.assertEqual(self.plugin_simple.license, None)
        self.assertEqual(self.plugin_name.license, 'MIT')

    def test_depreciation(self):
        """Check if depreciations raise as expected"""

        # check deprecation warning is firing
        with self.assertRaises(DeprecationWarning):
            self.assertEqual(self.plugin_old.name, 'OldPlugin')
            # check default value is used
            self.assertEqual(self.plugin_old.get_meta_value('ABC', 'ABCD', '123'), '123')
