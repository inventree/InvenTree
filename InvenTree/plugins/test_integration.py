""" Unit tests for integration plugins """

from django.test import TestCase
from django.conf import settings
from django.conf.urls import url, include

from plugins.integration import AppMixin, IntegrationPluginBase, SettingsMixin, UrlsMixin, NavigationMixin


class BaseMixinDefinition:
    def test_mixin_name(self):
        # mixin name
        self.assertEqual(self.mixin.registered_mixins[0]['key'], self.MIXIN_NAME)
        # human name
        self.assertEqual(self.mixin.registered_mixins[0]['human_name'], self.MIXIN_HUMAN_NAME)


class SettingsMixinTest(BaseMixinDefinition, TestCase):
    MIXIN_HUMAN_NAME = 'Settings'
    MIXIN_NAME = 'settings'
    MIXIN_ENABLE_CHECK = 'has_settings'

    TEST_SETTINGS = {'setting1': [1, 2, 3]}

    def setUp(self):
        class SettingsCls(SettingsMixin, IntegrationPluginBase):
            SETTINGS = self.TEST_SETTINGS
        self.mixin = SettingsCls()

        class NoSettingsCls(SettingsMixin, IntegrationPluginBase):
            pass
        self.mixin_nothing = NoSettingsCls()

    def test_function(self):
        # settings variable
        self.assertEqual(self.mixin.settings, self.TEST_SETTINGS)

        # settings pattern
        target_pattern = {f'PLUGIN_{self.mixin.slug.upper()}_{key}': value for key, value in self.mixin.settings.items()}
        self.assertEqual(self.mixin.settingspatterns, target_pattern)

        # no settings
        self.assertIsNone(self.mixin_nothing.settings)
        self.assertIsNone(self.mixin_nothing.settingspatterns)


class UrlsMixinTest(BaseMixinDefinition, TestCase):
    MIXIN_HUMAN_NAME = 'URLs'
    MIXIN_NAME = 'urls'
    MIXIN_ENABLE_CHECK = 'has_urls'

    def setUp(self):
        class UrlsCls(UrlsMixin, IntegrationPluginBase):
            def test():
                return 'ccc'
            URLS = [url('testpath', test, name='test'), ]
        self.mixin = UrlsCls()

        class NoUrlsCls(UrlsMixin, IntegrationPluginBase):
            pass
        self.mixin_nothing = NoUrlsCls()

    def test_function(self):
        plg_name = self.mixin.plugin_name()

        # base_url
        target_url = f'{settings.PLUGIN_URL}/{plg_name}/'
        self.assertEqual(self.mixin.base_url, target_url)

        # urlpattern
        target_pattern = url(f'^{plg_name}/', include((self.mixin.urls, plg_name)), name=plg_name)
        self.assertEqual(self.mixin.urlpatterns.reverse_dict, target_pattern.reverse_dict)

        # resolve the view
        self.assertEqual(self.mixin.urlpatterns.resolve('/testpath').func(), 'ccc')
        self.assertEqual(self.mixin.urlpatterns.reverse('test'), 'testpath')

        # no url
        self.assertIsNone(self.mixin_nothing.urls)
        self.assertIsNone(self.mixin_nothing.urlpatterns)


class AppMixinTest(BaseMixinDefinition, TestCase):
    MIXIN_HUMAN_NAME = 'App registration'
    MIXIN_NAME = 'app'
    MIXIN_ENABLE_CHECK = 'has_app'

    def setUp(self):
        class TestCls(AppMixin, IntegrationPluginBase):
            pass
        self.mixin = TestCls()

    def test_function(self):
        # test that this plugin is in settings
        self.assertIn('plugins.samples.integration', settings.INSTALLED_APPS)


class NavigationMixinTest(BaseMixinDefinition, TestCase):
    MIXIN_HUMAN_NAME = 'Navigation Links'
    MIXIN_NAME = 'navigation'
    MIXIN_ENABLE_CHECK = 'has_naviation'

    def setUp(self):
        class NavigationCls(NavigationMixin, IntegrationPluginBase):
            NAVIGATION = [
                {'name': 'aa', 'link': 'plugin:test:test_view'},
            ]
        self.mixin = NavigationCls()

    def test_function(self):
        # check right configuration
        self.assertEqual(self.mixin.navigation, [{'name': 'aa', 'link': 'plugin:test:test_view'}, ])
        # check wrong links fails
        with self.assertRaises(NotImplementedError):
            class NavigationCls(NavigationMixin, IntegrationPluginBase):
                NAVIGATION = ['aa', 'aa']
            NavigationCls()


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
            PUBLISH_DATE = "1111.11.11"
            VERSION = '1.2.3a'

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

        # pub_date
        self.assertEqual(self.plugin.pub_date, 'No date found')
        self.assertEqual(self.plugin_simple.pub_date, 'No date found')
        self.assertEqual(self.plugin_name.pub_date, "1111.11.11")

        # version
        self.assertEqual(self.plugin.version, None)
        self.assertEqual(self.plugin_simple.version, None)
        self.assertEqual(self.plugin_name.version, '1.2.3a')
