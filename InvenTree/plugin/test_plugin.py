"""Unit tests for plugins."""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

from django.test import TestCase, override_settings

import plugin.meta
import plugin.templatetags.plugin_extras as plugin_tags
from plugin import InvenTreePlugin, registry
from plugin.samples.integration.another_sample import (NoIntegrationPlugin,
                                                       WrongIntegrationPlugin)
from plugin.samples.integration.sample import SampleIntegrationPlugin


class PluginTagTests(TestCase):
    """Tests for the plugin extras."""

    def setUp(self):
        """Setup for all tests."""
        self.sample = SampleIntegrationPlugin()
        self.plugin_no = NoIntegrationPlugin()
        self.plugin_wrong = WrongIntegrationPlugin()

    def test_tag_plugin_list(self):
        """Test that all plugins are listed."""
        self.assertEqual(plugin_tags.plugin_list(), registry.plugins)

    def test_tag_inactive_plugin_list(self):
        """Test that all inactive plugins are listed."""
        self.assertEqual(plugin_tags.inactive_plugin_list(), registry.plugins_inactive)

    def test_tag_plugin_settings(self):
        """Check all plugins are listed."""
        self.assertEqual(
            plugin_tags.plugin_settings(self.sample),
            registry.mixins_settings.get(self.sample)
        )

    def test_tag_mixin_enabled(self):
        """Check that mixin enabled functions work."""
        key = 'urls'
        # mixin enabled
        self.assertEqual(plugin_tags.mixin_enabled(self.sample, key), True)

        # mixin not enabled
        self.assertEqual(plugin_tags.mixin_enabled(self.plugin_wrong, key), False)

        # mixin does not exist
        self.assertEqual(plugin_tags.mixin_enabled(self.plugin_no, key), False)

    def test_tag_safe_url(self):
        """Test that the safe url tag works expected."""
        # right url
        self.assertEqual(plugin_tags.safe_url('api-plugin-install'), '/api/plugins/install/')
        # wrong url
        self.assertEqual(plugin_tags.safe_url('indexas'), None)

    def test_tag_plugin_errors(self):
        """Test that all errors are listed."""
        self.assertEqual(plugin_tags.plugin_errors(), registry.errors)


class InvenTreePluginTests(TestCase):
    """Tests for InvenTreePlugin."""

    @classmethod
    def setUpTestData(cls):
        """Setup for all tests."""

        super().setUpTestData()

        cls.plugin = InvenTreePlugin()

        class NamedPlugin(InvenTreePlugin):
            """a named plugin."""
            NAME = 'abc123'

        cls.named_plugin = NamedPlugin()

        class SimpleInvenTreePlugin(InvenTreePlugin):
            NAME = 'SimplePlugin'

        cls.plugin_simple = SimpleInvenTreePlugin()

        class OldInvenTreePlugin(InvenTreePlugin):
            PLUGIN_SLUG = 'old'

        cls.plugin_old = OldInvenTreePlugin()

        class NameInvenTreePlugin(InvenTreePlugin):
            NAME = 'Aplugin'
            SLUG = 'a'
            TITLE = 'a titel'
            PUBLISH_DATE = "1111-11-11"
            AUTHOR = 'AA BB'
            DESCRIPTION = 'A description'
            VERSION = '1.2.3a'
            WEBSITE = 'https://aa.bb/cc'
            LICENSE = 'MIT'

        cls.plugin_name = NameInvenTreePlugin()
        cls.plugin_sample = SampleIntegrationPlugin()

        class VersionInvenTreePlugin(InvenTreePlugin):
            NAME = 'Version'

            MIN_VERSION = '0.1.0'
            MAX_VERSION = '0.1.3'

        cls.plugin_version = VersionInvenTreePlugin()

    def test_basic_plugin_init(self):
        """Check if a basic plugin intis."""
        self.assertEqual(self.plugin.NAME, '')
        self.assertEqual(self.plugin.plugin_name(), 'InvenTreePlugin')

    def test_basic_plugin_name(self):
        """Check if the name of a basic plugin can be set."""
        self.assertEqual(self.named_plugin.NAME, 'abc123')
        self.assertEqual(self.named_plugin.plugin_name(), 'abc123')

    def test_basic_is_active(self):
        """Check if a basic plugin is active."""
        self.assertEqual(self.plugin.is_active(), False)

    def test_action_name(self):
        """Check the name definition possibilities."""
        # plugin_name
        self.assertEqual(self.plugin.plugin_name(), 'InvenTreePlugin')
        self.assertEqual(self.plugin_simple.plugin_name(), 'SimplePlugin')
        self.assertEqual(self.plugin_name.plugin_name(), 'Aplugin')

        # is_sample
        self.assertEqual(self.plugin.is_sample, False)
        self.assertEqual(self.plugin_sample.is_sample, True)

        # slug
        self.assertEqual(self.plugin.slug, 'inventreeplugin')
        self.assertEqual(self.plugin_simple.slug, 'simpleplugin')
        self.assertEqual(self.plugin_name.slug, 'a')

        # human_name
        self.assertEqual(self.plugin.human_name, 'InvenTreePlugin')
        self.assertEqual(self.plugin_simple.human_name, 'SimplePlugin')
        self.assertEqual(self.plugin_name.human_name, 'a titel')

        # description
        self.assertEqual(self.plugin.description, 'InvenTreePlugin')
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
        self.assertEqual(self.plugin_name.website, 'https://aa.bb/cc')

        # license
        self.assertEqual(self.plugin.license, None)
        self.assertEqual(self.plugin_simple.license, None)
        self.assertEqual(self.plugin_name.license, 'MIT')

    def test_deprecation(self):
        """Check if DeprecationWarning is raised as expected."""
        with self.assertWarns(DeprecationWarning):
            self.assertEqual(self.plugin_old.slug, 'old')

    def test_version(self):
        """Test Version checks"""

        self.assertFalse(self.plugin_version.check_version([0, 0, 3]))
        self.assertTrue(self.plugin_version.check_version([0, 1, 0]))
        self.assertFalse(self.plugin_version.check_version([0, 1, 4]))

        plug = registry.plugins_full.get('version')
        self.assertEqual(plug.is_active(), False)


class RegistryTests(TestCase):
    """Tests for registry loading methods."""

    def mockDir(self) -> None:
        """Returns path to mock dir"""
        return str(Path(__file__).parent.joinpath('mock').absolute())

    def run_package_test(self, directory):
        """General runner for testing package based installs."""

        # Patch environment variable to add dir
        envs = {'INVENTREE_PLUGIN_TEST_DIR': directory}
        with mock.patch.dict(os.environ, envs):
            # Reload to rediscover plugins
            registry.reload_plugins(full_reload=True)

            # Depends on the meta set in InvenTree/plugin/mock/simple:SimplePlugin
            plg = registry.plugins_full.get('simple', None)
            self.assertIsNotNone(plg)
            self.assertEqual(plugin.meta.get_plugin_slug(plg), 'simple')
            self.assertEqual(plugin.meta.get_plugin_name(plg), 'SimplePlugin')

    def test_custom_loading(self):
        """Test if data in custom dir is loaded correctly."""
        test_dir = Path('plugin_test_dir')

        # Patch env
        envs = {'INVENTREE_PLUGIN_TEST_DIR': 'plugin_test_dir'}
        with mock.patch.dict(os.environ, envs):
            # Run plugin directory discovery again
            registry.plugin_dirs()

            # Check the directory was created
            self.assertTrue(test_dir.exists())

        # Clean folder up
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_subfolder_loading(self):
        """Test that plugins in subfolders get loaded."""
        self.run_package_test(self.mockDir())

    def test_folder_loading(self):
        """Test that plugins in folders outside of BASE_DIR get loaded."""

        # Run in temporary directory -> always a new random name
        with tempfile.TemporaryDirectory() as tmp:
            # Fill directory with sample data
            new_dir = Path(tmp).joinpath('mock')
            shutil.copytree(self.mockDir(), new_dir)

            # Run tests
            self.run_package_test(str(new_dir))

    @override_settings(PLUGIN_TESTING_SETUP=True)
    def test_package_loading(self):
        """Test that package distributed plugins work."""
        # Install sample package
        from plugin.installer import install_plugin

        # Install the plugin (this will reload the plugin registry)
        install_plugin(packagename='inventree-zapier')

        # Test that plugin was installed (but not yet activated)
        plg = registry.plugins_full.get('zapier', None)

        self.assertIsNotNone(plg)
        self.assertEqual(plugin.meta.get_plugin_slug(plg), 'zapier')
        self.assertEqual(plugin.meta.get_plugin_name(plg), 'inventree_zapier')
