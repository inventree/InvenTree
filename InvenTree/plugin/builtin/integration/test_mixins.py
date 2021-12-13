"""Unit tests for plugin mixins"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib.auth import get_user_model

from plugin import IntegrationPluginBase
from plugin.mixins import AppMixin, GlobalSettingsMixin, UrlsMixin, NavigationMixin
from plugin.urls import PLUGIN_BASE
from plugin.tests.test_integration import BaseMixinDefinition


class GlobalSettingsMixinTest(BaseMixinDefinition):
    MIXIN_HUMAN_NAME = 'Global settings'
    MIXIN_NAME = 'globalsettings'
    MIXIN_ENABLE_CHECK = 'has_globalsettings'

    TEST_SETTINGS = {'SETTING1': {'default': '123', }}

    def setUp(self):
        class SettingsCls(GlobalSettingsMixin, IntegrationPluginBase):
            GLOBALSETTINGS = self.TEST_SETTINGS
        self.mixin = SettingsCls()

        class NoSettingsCls(GlobalSettingsMixin, IntegrationPluginBase):
            pass
        self.mixin_nothing = NoSettingsCls()

        user = get_user_model()
        self.test_user = user.objects.create_user('testuser', 'test@testing.com', 'password')
        self.test_user.is_staff = True

    def test_function(self):
        # settings variable
        self.assertEqual(self.mixin.globalsettings, self.TEST_SETTINGS)

        # settings pattern
        target_pattern = {f'PLUGIN_{self.mixin.slug.upper()}_{key}': value for key, value in self.mixin.globalsettings.items()}
        self.assertEqual(self.mixin.globalsettingspatterns, target_pattern)

        # no settings
        self.assertIsNone(self.mixin_nothing.globalsettings)
        self.assertIsNone(self.mixin_nothing.globalsettingspatterns)

        # calling settings
        # not existing
        self.assertEqual(self.mixin.get_globalsetting('ABCD'), '')
        self.assertEqual(self.mixin_nothing.get_globalsetting('ABCD'), '')
        # right setting
        self.mixin.set_globalsetting('SETTING1', '12345', self.test_user)
        self.assertEqual(self.mixin.get_globalsetting('SETTING1'), '12345')
        # no setting
        self.assertEqual(self.mixin_nothing.get_globalsetting(''), '')


class UrlsMixinTest(BaseMixinDefinition):
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
        target_url = f'{PLUGIN_BASE}/{plg_name}/'
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

        # internal name
        self.assertEqual(self.mixin.internal_name, f'plugin:{self.mixin.slug}:')


class AppMixinTest(BaseMixinDefinition):
    MIXIN_HUMAN_NAME = 'App registration'
    MIXIN_NAME = 'app'
    MIXIN_ENABLE_CHECK = 'has_app'

    def setUp(self):
        class TestCls(AppMixin, IntegrationPluginBase):
            pass
        self.mixin = TestCls()

    def test_function(self):
        # test that this plugin is in settings
        self.assertIn('plugin.samples.integration', settings.INSTALLED_APPS)


class NavigationMixinTest(BaseMixinDefinition):
    MIXIN_HUMAN_NAME = 'Navigation Links'
    MIXIN_NAME = 'navigation'
    MIXIN_ENABLE_CHECK = 'has_naviation'

    def setUp(self):
        class NavigationCls(NavigationMixin, IntegrationPluginBase):
            NAVIGATION = [
                {'name': 'aa', 'link': 'plugin:test:test_view'},
            ]
            NAVIGATION_TAB_NAME = 'abcd1'
        self.mixin = NavigationCls()

        class NothingNavigationCls(NavigationMixin, IntegrationPluginBase):
            pass
        self.nothing_mixin = NothingNavigationCls()

    def test_function(self):
        # check right configuration
        self.assertEqual(self.mixin.navigation, [{'name': 'aa', 'link': 'plugin:test:test_view'}, ])
        # check wrong links fails
        with self.assertRaises(NotImplementedError):
            class NavigationCls(NavigationMixin, IntegrationPluginBase):
                NAVIGATION = ['aa', 'aa']
            NavigationCls()

        # navigation name
        self.assertEqual(self.mixin.navigation_name, 'abcd1')
        self.assertEqual(self.nothing_mixin.navigation_name, '')
