"""Unit tests for plugins."""

import os
import shutil
import subprocess
import tempfile
import textwrap
from datetime import datetime
from pathlib import Path
from unittest import mock
from unittest.mock import patch

from django.test import TestCase, override_settings

import plugin.templatetags.plugin_extras as plugin_tags
from InvenTree.unit_test import PluginRegistryMixin, TestQueryMixin
from plugin import InvenTreePlugin, PluginMixinEnum
from plugin.registry import registry
from plugin.samples.integration.another_sample import (
    NoIntegrationPlugin,
    WrongIntegrationPlugin,
)
from plugin.samples.integration.sample import SampleIntegrationPlugin

# Directory for testing plugins during CI
PLUGIN_TEST_DIR = '_testfolder/test_plugins'


class PluginTagTests(PluginRegistryMixin, TestCase):
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
            registry.mixins_settings.get(self.sample),
        )

    def test_tag_mixin_enabled(self):
        """Check that mixin enabled functions work."""
        key = 'urls'
        # mixin enabled
        self.assertEqual(plugin_tags.mixin_enabled(self.sample, key), True)
        # mixin not enabled
        self.assertEqual(plugin_tags.mixin_enabled(self.plugin_wrong, key), False)
        # mixin not existing
        self.assertEqual(plugin_tags.mixin_enabled(self.plugin_no, key), False)

    def test_mixin_available(self):
        """Check that mixin_available works."""
        from plugin import PluginMixinEnum

        self.assertEqual(plugin_tags.mixin_available(PluginMixinEnum.BARCODE), True)
        self.assertEqual(plugin_tags.mixin_available('wrong'), False)

    def test_tag_safe_url(self):
        """Test that the safe url tag works expected."""
        # right url
        self.assertEqual(
            plugin_tags.safe_url('api-plugin-install'), '/api/plugins/install/'
        )
        # wrong url
        self.assertEqual(plugin_tags.safe_url('indexas'), None)


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
            TITLE = 'a title'
            PUBLISH_DATE = '1111-11-11'
            AUTHOR = 'AA BB'
            DESCRIPTION = 'A description'
            VERSION = '1.2.3a'
            WEBSITE = 'https://aa.bb/cc'
            LICENSE = 'MIT'

        cls.plugin_name = NameInvenTreePlugin()

        class VersionInvenTreePlugin(InvenTreePlugin):
            NAME = 'Version'
            SLUG = 'testversion'

            MIN_VERSION = '0.1.0'
            MAX_VERSION = '0.1.3'

        cls.plugin_version = VersionInvenTreePlugin()

    def test_basic_plugin_init(self):
        """Check if a basic plugin intis."""
        self.assertEqual(self.plugin.NAME, '')
        self.assertEqual(self.plugin.plugin_name(), '')

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
        self.assertEqual(self.plugin.plugin_name(), '')
        self.assertEqual(self.plugin_simple.plugin_name(), 'SimplePlugin')
        self.assertEqual(self.plugin_name.plugin_name(), 'Aplugin')

        # is_sample
        self.assertEqual(self.plugin.is_sample, False)
        self.assertEqual(SampleIntegrationPlugin().is_sample, True)

        # slug
        self.assertEqual(self.plugin.slug, '')
        self.assertEqual(self.plugin_simple.slug, 'simpleplugin')
        self.assertEqual(self.plugin_name.slug, 'a')

        # human_name
        self.assertEqual(self.plugin.human_name, '')
        self.assertEqual(self.plugin_simple.human_name, 'SimplePlugin')
        self.assertEqual(self.plugin_name.human_name, 'a title')

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
        self.assertEqual(self.plugin_name.website, 'https://aa.bb/cc')

        # license
        self.assertEqual(self.plugin.license, None)
        self.assertEqual(self.plugin_simple.license, None)
        self.assertEqual(self.plugin_name.license, 'MIT')

    def test_depreciation(self):
        """Check if depreciations raise as expected."""
        # check deprecation warning is firing
        with self.assertWarns(DeprecationWarning):
            self.assertEqual(self.plugin_old.slug, 'old')
            # check default value is used
            self.assertEqual(
                self.plugin_old.get_meta_value('ABC', 'ABCD', '123'), '123'
            )

    def test_version(self):
        """Test Version checks."""
        self.assertFalse(self.plugin_version.check_version([0, 0, 3]))
        self.assertTrue(self.plugin_version.check_version([0, 1, 0]))
        self.assertFalse(self.plugin_version.check_version([0, 1, 4]))

        plug = registry.plugins_full.get('sampleversion')
        self.assertEqual(plug.is_active(), False)


class RegistryTests(TestQueryMixin, PluginRegistryMixin, TestCase):
    """Tests for registry loading methods."""

    def mockDir(self) -> str:
        """Returns path to mock dir."""
        return str(Path(__file__).parent.joinpath('mock').absolute())

    def run_package_test(self, directory):
        """General runner for testing package based installs."""
        # Patch environment variable to add dir
        envs = {'INVENTREE_PLUGIN_TEST_DIR': directory}
        with mock.patch.dict(os.environ, envs):
            # Reload to rediscover plugins
            registry.reload_plugins(full_reload=True, collect=True)
            registry.set_plugin_state('simple', True)

            # Depends on the meta set in InvenTree/plugin/mock/simple:SimplePlugin
            plg = registry.get_plugin('simple')
            self.assertEqual(plg.slug, 'simple')
            self.assertEqual(plg.human_name, 'SimplePlugin')

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
        subprocess.check_output(['pip', 'install', 'inventree-zapier'])

        # Reload to discover plugin
        registry.reload_plugins(full_reload=True, collect=True)

        # Test that plugin was installed
        plg = registry.get_plugin('zapier', active=None)
        self.assertEqual(plg.slug, 'zapier')
        self.assertEqual(plg.name, 'inventree_zapier')

    def test_broken_samples(self):
        """Test that the broken samples trigger reloads."""
        # In the base setup there are no errors
        self.assertEqual(len(registry.errors), 0)

        # Reload the registry with the broken samples dir
        brokenDir = str(Path(__file__).parent.joinpath('broken').absolute())
        with mock.patch.dict(os.environ, {'INVENTREE_PLUGIN_TEST_DIR': brokenDir}):
            # Reload to rediscover plugins
            registry.reload_plugins(full_reload=True, collect=True)

        self.assertEqual(len(registry.errors), 3)

        errors = registry.errors

        def find_error(group: str, key: str) -> str:
            """Find a matching error in the registry errors."""
            for error in errors.get(group, []):
                if key in error:
                    return error[key]
            return None

        # Check for expected errors in the registry
        self.assertIn(
            "Plugin 'BadActorPlugin' cannot override final method 'plugin_slug'",
            find_error('discovery', 'bad_actor'),
        )

        self.assertIn(
            "name 'bb' is not defined", find_error('discovery', 'broken_file')
        )

        self.assertIn(
            'This is a dummy error', find_error('Test:init_plugin', 'broken_sample')
        )

    def test_plugin_override(self):
        """Test that the plugin override works as expected."""
        with self.assertRaises(TypeError) as e:
            # Attempt to create a class which overrides the 'is_active' method
            class MyDummyPlugin(InvenTreePlugin):
                """A dummy plugin for testing."""

                NAME = 'MyDummyPlugin'
                SLUG = 'mydummyplugin'
                TITLE = 'My Dummy Plugin'
                VERSION = '1.0.0'

                def is_active(self):
                    """Override is_active to always return True."""
                    return True

                def __init_subclass__(cls):
                    """Override __init_subclass__."""
                    # Ensure that overriding the __init_subclass__ method
                    # does not prevent the TypeError from being raised

        # Check that the error message is as expected
        self.assertIn(
            "Plugin 'MyDummyPlugin' cannot override final method 'is_active' from InvenTreePlugin",
            str(e.exception),
        )

    @override_settings(PLUGIN_TESTING=True, PLUGIN_TESTING_SETUP=True)
    @patch.dict(os.environ, {'INVENTREE_PLUGIN_TEST_DIR': PLUGIN_TEST_DIR})
    def test_registry_reload(self):
        """Test that the registry correctly reloads plugin modules.

        - Create a simple plugin which we can change the version
        - Ensure that the "hash" of the plugin registry changes
        """
        dummy_file = os.path.join(PLUGIN_TEST_DIR, 'dummy_ci_plugin.py')

        # Ensure the plugin dir exists
        os.makedirs(PLUGIN_TEST_DIR, exist_ok=True)

        # Create an __init__.py file
        init_file = os.path.join(PLUGIN_TEST_DIR, '__init__.py')
        if not os.path.exists(init_file):
            with open(os.path.join(init_file), 'w', encoding='utf-8') as f:
                f.write('')

        def plugin_content(version):
            """Return the content of the plugin file."""
            content = f"""
            from plugin import InvenTreePlugin

            PLG_VERSION = "{version}"

            print(">>> LOADING DUMMY PLUGIN v" + PLG_VERSION + " <<<")

            class DummyCIPlugin(InvenTreePlugin):

                NAME = "DummyCIPlugin"
                SLUG = "dummyci"
                TITLE = "Dummy plugin for CI testing"

                VERSION = PLG_VERSION

            """

            return textwrap.dedent(content)

        def create_plugin_file(
            version: str, enabled: bool = True, reload: bool = True
        ) -> str:
            """Create a plugin file with the given version.

            Arguments:
                version: The version string to use for the plugin file
                enabled: Whether the plugin should be enabled or not
                reload: Whether to reload the plugin registry after creating the file

            Returns:
                str: The plugin registry hash
            """
            import time

            content = plugin_content(version)

            with open(dummy_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # Wait for the file to be written
            time.sleep(2)

            if reload:
                # Ensure the plugin is activated
                registry.set_plugin_state('dummyci', enabled)
                registry.reload_plugins(
                    full_reload=True, collect=True, force_reload=True
                )

            registry.update_plugin_hash()

            return registry.registry_hash

        # Initial hash, with plugin disabled
        hash_disabled = create_plugin_file('0.0.1', enabled=False, reload=False)

        # Perform initial registry reload
        registry.reload_plugins(full_reload=True, collect=True, force_reload=True)

        # Start plugin in known state
        registry.set_plugin_state('dummyci', False)

        hash_disabled = create_plugin_file('0.0.1', enabled=False)

        # Enable the plugin
        hash_enabled = create_plugin_file('0.1.0', enabled=True)

        # Hash must be different!
        self.assertNotEqual(hash_disabled, hash_enabled)

        plugin_hash = hash_enabled

        for v in ['0.1.1', '7.1.2', '1.2.1', '4.0.1']:
            h = create_plugin_file(v, enabled=True)
            self.assertNotEqual(plugin_hash, h)
            plugin_hash = h

        # Revert back to original 'version'
        h = create_plugin_file('0.1.0', enabled=True)
        self.assertEqual(hash_enabled, h)

        # Disable the plugin
        h = create_plugin_file('0.0.1', enabled=False)
        self.assertEqual(hash_disabled, h)

        # Finally, ensure that the plugin file is removed after testing
        os.remove(dummy_file)

    def test_check_reload(self):
        """Test that check_reload works as expected."""
        # Check that the registry is not reloaded
        self.assertFalse(registry.check_reload())

        with self.settings(TESTING=False, PLUGIN_TESTING_RELOAD=True):
            # Check that the registry is reloaded
            registry.reload_plugins(full_reload=True, collect=True, force_reload=True)
            self.assertFalse(registry.check_reload())

            # Check that changed hashes run through
            registry.registry_hash = 'abc'
            self.assertTrue(registry.check_reload())

    def test_builtin_mandatory_plugins(self):
        """Test that mandatory builtin plugins are always loaded."""
        from plugin.models import PluginConfig
        from plugin.registry import registry

        # Start with a 'clean slate'
        PluginConfig.objects.all().delete()

        registry.reload_plugins(full_reload=True, collect=True)
        mandatory = registry.MANDATORY_PLUGINS
        self.assertEqual(len(mandatory), 9)

        # Check that the mandatory plugins are loaded
        self.assertEqual(
            PluginConfig.objects.filter(active=True).count(), len(mandatory)
        )

        for key in mandatory:
            cfg = registry.get_plugin_config(key)
            self.assertIsNotNone(cfg, f"Mandatory plugin '{key}' not found in config")
            self.assertTrue(cfg.is_mandatory())
            self.assertTrue(cfg.active, f"Mandatory plugin '{key}' is not active")
            self.assertTrue(cfg.is_active())
            self.assertTrue(cfg.is_builtin())
            plg = registry.get_plugin(key)
            self.assertIsNotNone(plg, f"Mandatory plugin '{key}' not found")
            self.assertTrue(
                plg.is_mandatory, f"Plugin '{key}' is not marked as mandatory"
            )

        slug = 'bom-exporter'
        self.assertIn(slug, mandatory)
        cfg = registry.get_plugin_config(slug)

        # Try to disable the mandatory plugin
        cfg.active = False
        cfg.save()
        cfg.refresh_from_db()

        # Mandatory plugin cannot be disabled!
        self.assertTrue(cfg.active)
        self.assertTrue(cfg.is_active())

    def test_mandatory_plugins(self):
        """Test that plugins marked as 'mandatory' are always active."""
        from plugin.models import PluginConfig
        from plugin.registry import registry

        # Start with a 'clean slate'
        PluginConfig.objects.all().delete()

        self.assertEqual(PluginConfig.objects.count(), 0)

        registry.reload_plugins(full_reload=True, collect=True)

        N_CONFIG = PluginConfig.objects.count()
        N_ACTIVE = PluginConfig.objects.filter(active=True).count()

        # Run checks across the registered plugin configurations
        self.assertGreater(N_CONFIG, 0, 'No plugin configs found after reload')
        self.assertGreater(N_ACTIVE, 0, 'No active plugin configs found after reload')
        self.assertLess(
            N_ACTIVE, N_CONFIG, 'All plugins are installed, but only some are active'
        )
        self.assertEqual(
            N_ACTIVE,
            len(registry.MANDATORY_PLUGINS),
            'Not all mandatory plugins are active',
        )

        # Next, mark some additional plugins as mandatory
        # These are a mix of "builtin" and "sample" plugins
        mandatory_slugs = ['sampleui', 'validator', 'digikeyplugin', 'autocreatebuilds']

        with self.settings(PLUGINS_MANDATORY=mandatory_slugs):
            # Reload the plugins to apply the mandatory settings
            registry.reload_plugins(full_reload=True, collect=True)

            self.assertEqual(N_CONFIG, PluginConfig.objects.count())
            self.assertEqual(
                N_ACTIVE + 4, PluginConfig.objects.filter(active=True).count()
            )

            # Check that the mandatory plugins are active
            for slug in mandatory_slugs:
                cfg = registry.get_plugin_config(slug)
                self.assertIsNotNone(
                    cfg, f"Mandatory plugin '{slug}' not found in config"
                )
                self.assertTrue(cfg.is_mandatory())
                self.assertTrue(cfg.active, f"Mandatory plugin '{slug}' is not active")
                self.assertTrue(cfg.is_active())
                plg = registry.get_plugin(slug)
                self.assertTrue(plg.is_active(), f"Plugin '{slug}' is not active")
                self.assertIsNotNone(plg, f"Mandatory plugin '{slug}' not found")
                self.assertTrue(
                    plg.is_mandatory, f"Plugin '{slug}' is not marked as mandatory"
                )

    def test_with_mixin(self):
        """Tests for the 'with_mixin' registry method."""
        from plugin.models import PluginConfig
        from plugin.registry import registry

        self.ensurePluginsLoaded()

        N_CONFIG = PluginConfig.objects.count()
        self.assertGreater(N_CONFIG, 0, 'No plugin configs found')

        # Test that the 'with_mixin' method is query efficient
        for mixin in PluginMixinEnum:
            with self.assertNumQueriesLessThan(3):
                registry.with_mixin(mixin)

        # Test for the 'base' mixin - we expect that this returns "all" plugins
        base = registry.with_mixin(PluginMixinEnum.BASE, active=None, builtin=None)
        self.assertEqual(len(base), N_CONFIG, 'Base mixin does not return all plugins')

        # Next, fetch only "active" plugins
        n_active = len(registry.with_mixin(PluginMixinEnum.BASE, active=True))
        self.assertGreater(n_active, 0, 'No active plugins found with base mixin')
        self.assertLess(n_active, N_CONFIG, 'All plugins are active with base mixin')

        n_inactive = len(registry.with_mixin(PluginMixinEnum.BASE, active=False))

        self.assertGreater(n_inactive, 0, 'No inactive plugins found with base mixin')
        self.assertLess(n_inactive, N_CONFIG, 'All plugins are active with base mixin')
        self.assertEqual(
            n_active + n_inactive, N_CONFIG, 'Active and inactive plugins do not match'
        )

        # Filter by 'builtin' status
        plugins = registry.with_mixin(PluginMixinEnum.LABELS, builtin=True, active=True)
        self.assertEqual(len(plugins), 2)

        keys = [p.slug for p in plugins]
        self.assertIn('inventreelabel', keys)
        self.assertIn('inventreelabelmachine', keys)

    def test_config_attributes(self):
        """Test attributes for PluginConfig objects."""
        # Get the plugin config for the 'sampleui' plugin
        cfg = registry.get_plugin_config('sampleui')
        self.assertIsNotNone(cfg, 'PluginConfig for sampleui not found')

        self.assertFalse(cfg.is_mandatory())
        self.assertFalse(cfg.is_active())
        self.assertFalse(cfg.is_builtin())
        self.assertFalse(cfg.is_package())
        self.assertTrue(cfg.is_sample())
