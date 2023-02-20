"""Tests for general API tests for the plugin app."""

from django.urls import reverse

from rest_framework.exceptions import NotFound

from common.models import WebConnection
from InvenTree.api_tester import InvenTreeAPITestCase, PluginMixin
from plugin import registry
from plugin.api import check_plugin
from plugin.base.supplier.models import ConnectionSetting
from plugin.models import PluginConfig
from plugin.samples.supplier.supplier_sample import SampleSupplierPlugin


class PluginDetailAPITest(PluginMixin, InvenTreeAPITestCase):
    """Tests the plugin API endpoints."""

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

    def test_plugin_url(self):
        """Test API url."""
        self.assertEqual(PluginConfig.objects.all().first().get_api_url(), '/api/plugins/')

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

        self.assertEqual(data['success'], True)

        # valid - github url
        data = self.post(
            url,
            {
                'confirm': True,
                'url': self.PKG_URL
            },
            expected_code=201,
        ).data
        self.assertEqual(data['success'], True)

        # valid - github url and packagename
        data = self.post(
            url,
            {
                'confirm': True,
                'url': self.PKG_URL,
                'packagename': 'minimal',
            },
            expected_code=201,
        ).data
        self.assertEqual(data['success'], True)

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

        test_plg = self.plugin_confs.first()

        def assert_plugin_active(self, active):
            self.assertEqual(PluginConfig.objects.all().first().active, active)

        # Should not work - not a superuser
        response = self.client.post(reverse('api-plugin-activate'), {}, follow=True)
        self.assertEqual(response.status_code, 403)

        # Make user superuser
        self.user.is_superuser = True
        self.user.save()

        # Deactivate plugin
        test_plg.active = False
        test_plg.save()

        # Activate plugin with detail url
        assert_plugin_active(self, False)
        response = self.client.patch(reverse('api-plugin-detail-activate', kwargs={'pk': test_plg.id}), {}, follow=True)
        self.assertEqual(response.status_code, 200)
        assert_plugin_active(self, True)

        # Deactivate plugin
        test_plg.active = False
        test_plg.save()

        # Activate plugin
        assert_plugin_active(self, False)
        response = self.client.patch(reverse('api-plugin-activate'), {'pk': test_plg.pk}, follow=True)
        self.assertEqual(response.status_code, 200)
        assert_plugin_active(self, True)

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

        # deactivate plugin - deactivate again -> nothing will hapen but the nothing 'changed' function is triggered
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

        # check reload on save
        with self.assertWarns(Warning) as cm:
            plg_inactive = self.plugin_confs.filter(active=False).first()
            plg_inactive.active = True
            plg_inactive.save()
        self.assertEqual(cm.warning.args[0], 'A reload was triggered')

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


class WebConnectionSettingDetailTest(PluginMixin, InvenTreeAPITestCase):
    """Tests the web connection API endpoints."""

    def test_plugin_url(self):
        """Test API url."""
        # Make user as superuser
        self.user.is_superuser = True
        self.user.save()

        PLUGIN_NAME = 'samplesupplier'
        SETTING_NAME = 'SETTING_A'
        CONNECTION_KEY = 'sample_account'
        CONNECTION_NAME = '1'
        PLUGIN = registry.get_plugin(PLUGIN_NAME).db

        def test_url(setting=SETTING_NAME, key=CONNECTION_KEY, name=CONNECTION_NAME):
            return reverse(
                'api-plugin-webconnection-setting-detail',
                kwargs={'plugin': PLUGIN_NAME, 'connection_key': key, 'connection': name, 'key': setting}
            )

        # Test endpoint to create connection
        rsp = self.post(reverse('api-plugin-connection-list'), {'plugin': PLUGIN.pk, 'connection_key': CONNECTION_KEY}, expected_code=201)
        self.assertEqual(rsp.data['plugin'], PLUGIN.pk)
        self.assertEqual(rsp.data['connection_key'], CONNECTION_KEY)
        self.assertEqual(rsp.data['creator'], self.user.username)

        # Create connection
        con = WebConnection.objects.create(plugin=PLUGIN, connection_key=CONNECTION_KEY, name=CONNECTION_NAME,)
        ConnectionSetting.objects.create(plugin=PLUGIN, connection_key=CONNECTION_KEY, connection=con, key=SETTING_NAME)

        # Detail endpoint
        # Test not active plugin - should fail
        resp = self.get(test_url(), expected_code=404)
        self.assertEqual(resp.json()['detail'], f"Plugin '{PLUGIN_NAME}' is not active")

        # Activate plugin
        PLUGIN.active = True
        PLUGIN.save()
        # Test active plugin - should work
        data = self.get(test_url(), expected_code=200).data
        self.assertEqual(data['key'], SETTING_NAME)
        self.assertEqual(data['description'], SampleSupplierPlugin.CONNECTIONS[CONNECTION_KEY].settings[SETTING_NAME]['description'])

        # Test wrong connectionkey - should fail
        resp = self.get(test_url(key='wrong'), expected_code=404)
        self.assertEqual(resp.json()['detail'], f"Plugin '{PLUGIN_NAME}' has no connection_key matching 'wrong'")

        # Test wrong key - should fail
        resp = self.get(test_url(setting='wrong'), expected_code=404)
        self.assertEqual(resp.json()['detail'], f"Plugin '{PLUGIN_NAME}' connection_key '{CONNECTION_KEY}' has no setting matching 'wrong'")
