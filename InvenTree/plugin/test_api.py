# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase


class PluginDetailAPITest(InvenTreeAPITestCase):
    """
    Tests the plugin AP I endpoints
    """

    roles = [
        'admin.add',
        'admin.view',
        'admin.change',
        'admin.delete',
    ]

    def setUp(self):
        self.MSG_NO_PKG = 'Either packagenmae of url must be provided'

        self.PKG_NAME = 'minimal'
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
        from plugin import plugin_reg

        url = reverse('admin:plugin_pluginconfig_changelist')
        fixtures = PluginConfig.objects.all()

        # check if plugins were registered -> in some test setups the startup has no db access
        if not fixtures:
            plugin_reg.reload_plugins()
            fixtures = PluginConfig.objects.all()

        print([str(a) for a in fixtures])
        fixtures = fixtures[0:1]
        # deactivate plugin
        self.post(url, {
            'action': 'plugin_deactivate',
            '_selected_action': [f.pk for f in fixtures],
        }, expected_code=200)

        # deactivate plugin - deactivate again -> nothing will hapen but the nothing 'changed' function is triggered
        self.post(url, {
            'action': 'plugin_deactivate',
            '_selected_action': [f.pk for f in fixtures],
        }, expected_code=200)

        # activate plugin
        self.post(url, {
            'action': 'plugin_activate',
            '_selected_action': [f.pk for f in fixtures],
        }, expected_code=200)
