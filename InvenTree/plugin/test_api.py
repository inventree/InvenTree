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
        data = self.post(url, {
            'packagename': self.PKG_NAME
        }, expected_code=400).data
