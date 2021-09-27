""" Unit tests for integration plugins """

from django.test import TestCase
from django.conf import settings
from django.conf.urls import url, include

from plugins.integration import IntegrationPlugin, MixinBase, SettingsMixin, UrlsMixin, NavigationMixin
import part.templatetags.plugin_extras as plugin_tags


class BaseMixinDefinition:
    def test_mixin_name(self):
        # mixin name
        self.assertEqual(self.mixin.registered_mixins[0]['key'], self.MIXIN_NAME)
        # human name
        self.assertEqual(self.mixin.registered_mixins[0]['human_name'], self.MIXIN_HUMAN_NAME)
        # mixin check
        #  self.assertEqual(self.mixin.plugin_name(), self.MIXIN_ENABLE_CHECK)


class SettingsMixinTest(BaseMixinDefinition, TestCase):
    MIXIN_HUMAN_NAME = 'Settings'
    MIXIN_NAME = 'settings'
    MIXIN_ENABLE_CHECK = 'has_settings'

    TEST_SETTINGS = {'setting1': [1, 2, 3]}

    def setUp(self):
        class cls(SettingsMixin, IntegrationPlugin):
            SETTINGS = self.TEST_SETTINGS
        self.mixin = cls()

    def test_function(self):
        # settings variable
        self.assertEqual(self.mixin.settings, self.TEST_SETTINGS)
        # settings pattern
        target_pattern = {f'PLUGIN_{self.mixin.plugin_name().upper()}_{key}': value for key, value in self.mixin.settings.items()}
        self.assertEqual(self.mixin.settingspatterns, target_pattern)


class UrlsMixinTest(BaseMixinDefinition, TestCase):
    MIXIN_HUMAN_NAME = 'URLs'
    MIXIN_NAME = 'urls'
    MIXIN_ENABLE_CHECK = 'has_urls'

    def setUp(self):
        class cls(UrlsMixin, IntegrationPlugin):
            def test(self):
                return 'ccc'
            URLS = [url('test', test, name='test'),]
        self.mixin = cls()

    def test_function(self):
        plg_name = self.mixin.plugin_name()

        # base_url
        target_url = f'{settings.PLUGIN_URL}/{plg_name}/'
        self.assertEqual(self.mixin.base_url, target_url)

        # urlpattern
        target_pattern = url(f'^{plg_name}/', include((self.mixin.urls, plg_name)), name=plg_name)
        self.assertEqual(self.mixin.urlpatterns.reverse_dict, target_pattern.reverse_dict)


class NavigationMixinTest(BaseMixinDefinition, TestCase):
    MIXIN_HUMAN_NAME = 'Navigation Links'
    MIXIN_NAME = 'navigation'
    MIXIN_ENABLE_CHECK = 'has_naviation'

    def setUp(self):
        class cls(NavigationMixin, IntegrationPlugin):
            NAVIGATION = [
                {'name': 'aa', 'link': 'plugin:test:test_view'},
            ]
        self.mixin = cls()

    def test_function(self):
        # check right configuration
        self.assertEqual(self.mixin.navigation, [{'name': 'aa', 'link': 'plugin:test:test_view'},])
        # check wrong links fails
        with self.assertRaises(NotImplementedError):
            class cls(NavigationMixin, IntegrationPlugin):
                NAVIGATION = ['aa', 'aa']
            cls()
