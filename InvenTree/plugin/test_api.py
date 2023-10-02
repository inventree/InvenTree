"""Tests for general API tests for the plugin app."""

from django.urls import reverse

from rest_framework.exceptions import NotFound

from InvenTree.unit_test import InvenTreeAPITestCase, PluginMixin
from plugin.api import check_plugin
from plugin.models import PluginConfig
from plugin.registry import registry


class PluginDetailAPITest(PluginMixin, InvenTreeAPITestCase):
    """Tests the plugin API endpoints"""

    roles = [
        'admin.add',
        'admin.view',
        'admin.change',
        'admin.delete',
    ]

    def setUp(self):
        """Setup for all tests."""
        self.MSG_NO_PKG = 'Either packagename of URL must be provided'

        self.PKG_NAME = 'minimal'
        self.PKG_URL = 'git+https://github.com/geoffrey-a-reed/minimal'
        super().setUp()

    def test_plugin_install(self):
        """Test the plugin install command."""
        url = reverse('api-plugin-install')

        # valid - Pypi
        data = self.post(
            url,
            {
                'confirm': True,
                'packagename': self.PKG_NAME
            },
            expected_code=201,
        ).data

        self.assertEqual(data['success'], "Installed plugin successfully")

        # valid - github url
        data = self.post(
            url,
            {
                'confirm': True,
                'url': self.PKG_URL
            },
            expected_code=201,
        ).data

        self.assertEqual(data['success'], "Installed plugin successfully")

        # valid - github url and package name
        data = self.post(
            url,
            {
                'confirm': True,
                'url': self.PKG_URL,
                'packagename': 'minimal',
            },
            expected_code=201,
        ).data

        self.assertEqual(data['success'], "Installed plugin successfully")
        self.assertIn('result', data)

        # invalid tries
        # no input
        self.post(url, {}, expected_code=400)

        # no package info
        data = self.post(url, {
            'confirm': True,
        }, expected_code=400).data

        self.assertEqual(data['url'][0].title().upper(), self.MSG_NO_PKG.upper())
        self.assertEqual(data['packagename'][0].title().upper(), self.MSG_NO_PKG.upper())

        # not confirmed
        self.post(url, {
            'packagename': self.PKG_NAME
        }, expected_code=400)

        data = self.post(url, {
            'packagename': self.PKG_NAME,
            'confirm': False,
        }, expected_code=400).data

        self.assertEqual(data['confirm'][0].title().upper(), 'Installation not confirmed'.upper())

    def test_plugin_activate(self):
        """Test the plugin activate."""

        registry.set_plugin_state('sample', False)

        # Find the first available inactive plugin
        cfg = PluginConfig.objects.filter(active=False).first()
        slug = cfg.key

        self.assertFalse(registry.get_plugin_state(slug))

        self.user.is_superuser = False
        self.user.save()

        # Should not work - not a superuser
        response = self.client.post(reverse('api-plugin-activate'), {}, follow=True)
        self.assertEqual(response.status_code, 403)

        # Make user superuser
        self.user.is_superuser = True
        self.user.save()

        # Activate plugin with detail url
        response = self.client.patch(reverse('api-plugin-detail-activate', kwargs={'pk': cfg.pk}), {}, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(registry.get_plugin_state(slug))

        # Deactivate plugin
        registry.set_plugin_state(slug, False)
        self.assertFalse(registry.get_plugin_state(slug))

        # Activate plugin
        response = self.client.patch(reverse('api-plugin-activate'), {'pk': cfg.pk}, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(registry.get_plugin_state(slug))

    def test_admin_action(self):
        """Test the PluginConfig action commands."""
        url = reverse('admin:plugin_pluginconfig_changelist')

        test_plg = self.plugin_confs.first()
        # deactivate plugin
        response = self.client.post(url, {
            'action': 'plugin_deactivate',
            'index': 0,
            '_selected_action': [test_plg.pk],
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        # deactivate plugin - deactivate again -> nothing will happen but the nothing 'changed' function is triggered
        response = self.client.post(url, {
            'action': 'plugin_deactivate',
            'index': 0,
            '_selected_action': [test_plg.pk],
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        # activate plugin
        response = self.client.post(url, {
            'action': 'plugin_activate',
            'index': 0,
            '_selected_action': [test_plg.pk],
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        # save to deactivate a plugin
        response = self.client.post(reverse('admin:plugin_pluginconfig_change', args=(test_plg.pk, )), {
            '_save': 'Save',
        }, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_model(self):
        """Test the PluginConfig model."""
        # check mixin registry
        plg = self.plugin_confs.first()
        mixin_dict = plg.mixins()
        self.assertIn('base', mixin_dict)
        self.assertDictContainsSubset({'base': {'key': 'base', 'human_name': 'base'}}, mixin_dict)

        plg_inactive = self.plugin_confs.filter(active=False).first()
        plg_inactive.active = False
        plg_inactive.save()

        # check reload on save (hash will be different)
        reg_hash = registry.calculate_plugin_hash()

        plg_inactive.active = True
        plg_inactive.save()

        # Check that the registry hash has changed (because we have reloaded the plugin registry)
        self.assertNotEqual(reg_hash, registry.calculate_plugin_hash())

    def test_check_plugin(self):
        """Test check_plugin function."""

        # No argument
        with self.assertRaises(NotFound) as exc:
            check_plugin(plugin_slug=None, plugin_pk=None)
        self.assertEqual(str(exc.exception.detail), 'Plugin not specified')

        # Wrong with slug
        with self.assertRaises(NotFound) as exc:
            check_plugin(plugin_slug='123abc', plugin_pk=None)
        self.assertEqual(str(exc.exception.detail), "Plugin '123abc' not installed")

        # Wrong with pk
        with self.assertRaises(NotFound) as exc:
            check_plugin(plugin_slug=None, plugin_pk='123')
        self.assertEqual(str(exc.exception.detail), "Plugin '123' not installed")

    def test_plugin_settings(self):
        """Test plugin settings access via the API"""

        # Ensure we have superuser permissions
        self.user.is_superuser = True
        self.user.save()

        # Activate the 'sample' plugin via the API
        cfg = PluginConfig.objects.filter(key='sample').first()
        url = reverse('api-plugin-detail-activate', kwargs={'pk': cfg.pk})
        self.client.patch(url, {}, expected_code=200)

        # Valid plugin settings endpoints
        valid_settings = [
            'SELECT_PART',
            'API_KEY',
            'NUMERICAL_SETTING',
        ]

        for key in valid_settings:
            response = self.get(
                reverse('api-plugin-setting-detail', kwargs={
                    'plugin': 'sample',
                    'key': key
                }))

            self.assertEqual(response.data['key'], key)

        # Test that an invalid setting key raises a 404 error
        response = self.get(
            reverse('api-plugin-setting-detail', kwargs={
                'plugin': 'sample',
                'key': 'INVALID_SETTING'
            }),
            expected_code=404
        )

        # Test that a protected setting returns hidden value
        response = self.get(
            reverse('api-plugin-setting-detail', kwargs={
                'plugin': 'sample',
                'key': 'PROTECTED_SETTING'
            }),
            expected_code=200
        )

        self.assertEqual(response.data['value'], '***')

        # Test that we can update a setting value
        response = self.patch(
            reverse('api-plugin-setting-detail', kwargs={
                'plugin': 'sample',
                'key': 'NUMERICAL_SETTING'
            }),
            {
                'value': 456
            },
            expected_code=200
        )

        self.assertEqual(response.data['value'], '456')

        # Retrieve the value again
        response = self.get(
            reverse('api-plugin-setting-detail', kwargs={
                'plugin': 'sample',
                'key': 'NUMERICAL_SETTING'
            }),
            expected_code=200
        )

        self.assertEqual(response.data['value'], '456')
