# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase


class PluginDetailAPITest(InvenTreeAPITestCase):
    """
    Tests the plugin API endpoints
    """

    roles = [
        'admin.add',
        'admin.view',
        'admin.change',
        'admin.delete',
    ]

    def setUp(self):
        self.MSG_NO_PKG = 'Either packagename of URL must be provided'

        self.PKG_NAME = 'minimal'
        self.PKG_URL = 'git+https://github.com/geoffrey-a-reed/minimal'
        super().setUp()

    def test_plugin_install(self):
        """
        Test the plugin install command
        """
        url = reverse('api-plugin-install')

        # valid - Pypi
        data = self.post(url, {
            'confirm': True,
            'packagename': self.PKG_NAME
        }, expected_code=201).data
        self.assertEqual(data['success'], True)

        # valid - github url
        data = self.post(url, {
            'confirm': True,
            'url': self.PKG_URL
        }, expected_code=201).data
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
        }, expected_code=400).data
        data = self.post(url, {
            'packagename': self.PKG_NAME,
            'confirm': False,
        }, expected_code=400).data
        self.assertEqual(data['confirm'][0].title().upper(), 'Installation not confirmed'.upper())

    def test_admin_action(self):
        """
        Test the PluginConfig action commands
        """
        from plugin.models import PluginConfig
        from plugin import registry

        url = reverse('admin:plugin_pluginconfig_changelist')
        fixtures = PluginConfig.objects.all()

        # check if plugins were registered -> in some test setups the startup has no db access
        print(f'[PLUGIN-TEST] currently {len(fixtures)} plugin entries found')
        if not fixtures:
            registry.reload_plugins()
            fixtures = PluginConfig.objects.all()
            print(f'Reloaded plugins - now {len(fixtures)} entries found')

        print([str(a) for a in fixtures])
        fixtures = fixtures[0:1]
        # deactivate plugin
        response = self.client.post(url, {
            'action': 'plugin_deactivate',
            'index': 0,
            '_selected_action': [f.pk for f in fixtures],
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        # deactivate plugin - deactivate again -> nothing will hapen but the nothing 'changed' function is triggered
        response = self.client.post(url, {
            'action': 'plugin_deactivate',
            'index': 0,
            '_selected_action': [f.pk for f in fixtures],
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        # activate plugin
        response = self.client.post(url, {
            'action': 'plugin_activate',
            'index': 0,
            '_selected_action': [f.pk for f in fixtures],
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        # activate everything
        fixtures = PluginConfig.objects.all()
        response = self.client.post(url, {
            'action': 'plugin_activate',
            'index': 0,
            '_selected_action': [f.pk for f in fixtures],
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        fixtures = PluginConfig.objects.filter(active=True)
        # save to deactivate a plugin
        response = self.client.post(reverse('admin:plugin_pluginconfig_change', args=(fixtures.first().pk, )), {
            '_save': 'Save',
        }, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_model(self):
        """
        Test the PluginConfig model
        """
        from plugin.models import PluginConfig
        from plugin import registry

        fixtures = PluginConfig.objects.all()

        # check if plugins were registered
        if not fixtures:
            registry.reload_plugins()
            fixtures = PluginConfig.objects.all()

        # check mixin registry
        plg = fixtures.first()
        mixin_dict = plg.mixins()
        self.assertIn('base', mixin_dict)
        self.assertDictContainsSubset({'base':{'key':'base', 'human_name':'base'}}, mixin_dict)

        # check reload on save
        with self.assertWarns('A reload was triggered'):
            plg_inactive = fixtures.filter(active=False).first()
            plg_inactive.active = True
            plg_inactive.save()
        print('done')
