""" Unit tests for integration plugins """
from datetime import datetime

from django.test import TestCase

from plugin import IntegrationPluginBase


class BaseMixinDefinition(TestCase):
    def test_mixin_name(self):
        # mixin name
        self.assertEqual(self.mixin.registered_mixins[0]['key'], self.MIXIN_NAME)
        # human name
        self.assertEqual(self.mixin.registered_mixins[0]['human_name'], self.MIXIN_HUMAN_NAME)


class IntegrationPluginBaseTests(TestCase):
    """ Tests for IntegrationPluginBase """

    def setUp(self):
        self.plugin = IntegrationPluginBase()

        class SimpeIntegrationPluginBase(IntegrationPluginBase):
            PLUGIN_NAME = 'SimplePlugin'

        self.plugin_simple = SimpeIntegrationPluginBase()

        class NameIntegrationPluginBase(IntegrationPluginBase):
            PLUGIN_NAME = 'Aplugin'
            PLUGIN_SLUG = 'a'
            PLUGIN_TITLE = 'a titel'
            PUBLISH_DATE = "1111-11-11"
            AUTHOR = 'AA BB'
            DESCRIPTION = 'A description'
            VERSION = '1.2.3a'
            WEBSITE = 'http://aa.bb/cc'
            LICENSE = 'MIT'

        self.plugin_name = NameIntegrationPluginBase()

    def test_action_name(self):
        """check the name definition possibilities"""
        # plugin_name
        self.assertEqual(self.plugin.plugin_name(), '')
        self.assertEqual(self.plugin_simple.plugin_name(), 'SimplePlugin')
        self.assertEqual(self.plugin_name.plugin_name(), 'Aplugin')

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
