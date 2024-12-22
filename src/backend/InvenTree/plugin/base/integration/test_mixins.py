"""Unit tests for base mixins for plugins."""

import os

from django.conf import settings
from django.test import TestCase
from django.urls import include, path, re_path

from InvenTree.unit_test import InvenTreeTestCase
from plugin import InvenTreePlugin
from plugin.helpers import MixinNotImplementedError
from plugin.mixins import (
    APICallMixin,
    AppMixin,
    NavigationMixin,
    SettingsMixin,
    UrlsMixin,
)
from plugin.urls import PLUGIN_BASE


class BaseMixinDefinition:
    """Mixin to test the meta functions of all mixins."""

    def test_mixin_name(self):
        """Test that the mixin registers itseld correctly."""
        # mixin name
        self.assertIn(
            self.MIXIN_NAME,
            {item['key'] for item in self.mixin.registered_mixins.values()},
        )
        # human name
        self.assertIn(
            self.MIXIN_HUMAN_NAME,
            {item['human_name'] for item in self.mixin.registered_mixins.values()},
        )


class SettingsMixinTest(BaseMixinDefinition, InvenTreeTestCase):
    """Tests for SettingsMixin."""

    MIXIN_HUMAN_NAME = 'Settings'
    MIXIN_NAME = 'settings'
    MIXIN_ENABLE_CHECK = 'has_settings'

    TEST_SETTINGS = {'SETTING1': {'default': '123'}}

    def setUp(self):
        """Setup for all tests."""

        class SettingsCls(SettingsMixin, InvenTreePlugin):
            SETTINGS = self.TEST_SETTINGS

        self.mixin = SettingsCls()

        class NoSettingsCls(SettingsMixin, InvenTreePlugin):
            pass

        self.mixin_nothing = NoSettingsCls()

        super().setUp()

    def test_function(self):
        """Test that the mixin functions."""
        # settings variable
        self.assertEqual(self.mixin.settings, self.TEST_SETTINGS)

        # calling settings
        # not existing
        self.assertEqual(self.mixin.get_setting('ABCD'), '')
        self.assertEqual(self.mixin_nothing.get_setting('ABCD'), '')

        # right setting
        self.mixin.set_setting('SETTING1', '12345', self.user)
        self.assertEqual(self.mixin.get_setting('SETTING1'), '12345')

        # no setting
        self.assertEqual(self.mixin_nothing.get_setting(''), '')


class UrlsMixinTest(BaseMixinDefinition, TestCase):
    """Tests for UrlsMixin."""

    MIXIN_HUMAN_NAME = 'URLs'
    MIXIN_NAME = 'urls'
    MIXIN_ENABLE_CHECK = 'has_urls'

    def setUp(self):
        """Setup for all tests."""

        class UrlsCls(UrlsMixin, InvenTreePlugin):
            def test():
                return 'ccc'

            URLS = [path('testpath', test, name='test')]

        self.mixin = UrlsCls()

        class NoUrlsCls(UrlsMixin, InvenTreePlugin):
            pass

        self.mixin_nothing = NoUrlsCls()

    def test_function(self):
        """Test that the mixin functions."""
        plg_name = self.mixin.plugin_name()

        # base_url
        target_url = f'{PLUGIN_BASE}/{plg_name}/'
        self.assertEqual(self.mixin.base_url, target_url)

        # urlpattern
        target_pattern = re_path(
            f'^{plg_name}/', include((self.mixin.urls, plg_name)), name=plg_name
        )
        self.assertEqual(
            self.mixin.urlpatterns.reverse_dict, target_pattern.reverse_dict
        )

        # resolve the view
        self.assertEqual(self.mixin.urlpatterns.resolve('/testpath').func(), 'ccc')
        self.assertEqual(self.mixin.urlpatterns.reverse('test'), 'testpath')

        # no url
        self.assertIsNone(self.mixin_nothing.urls)
        self.assertIsNone(self.mixin_nothing.urlpatterns)

        # internal name
        self.assertEqual(self.mixin.internal_name, f'plugin:{self.mixin.slug}:')


class AppMixinTest(BaseMixinDefinition, TestCase):
    """Tests for AppMixin."""

    MIXIN_HUMAN_NAME = 'App registration'
    MIXIN_NAME = 'app'
    MIXIN_ENABLE_CHECK = 'has_app'

    def setUp(self):
        """Setup for all tests."""

        class TestCls(AppMixin, InvenTreePlugin):
            pass

        self.mixin = TestCls()

    def test_function(self):
        """Test that the sample plugin registers in settings."""
        self.assertIn('plugin.samples.integration', settings.INSTALLED_APPS)


class NavigationMixinTest(BaseMixinDefinition, TestCase):
    """Tests for NavigationMixin."""

    MIXIN_HUMAN_NAME = 'Navigation Links'
    MIXIN_NAME = 'navigation'
    MIXIN_ENABLE_CHECK = 'has_naviation'

    def setUp(self):
        """Setup for all tests."""

        class NavigationCls(NavigationMixin, InvenTreePlugin):
            NAVIGATION = [{'name': 'aa', 'link': 'plugin:test:test_view'}]
            NAVIGATION_TAB_NAME = 'abcd1'

        self.mixin = NavigationCls()

        class NothingNavigationCls(NavigationMixin, InvenTreePlugin):
            pass

        self.nothing_mixin = NothingNavigationCls()

    def test_function(self):
        """Test that a correct configuration functions."""
        # check right configuration
        self.assertEqual(
            self.mixin.navigation, [{'name': 'aa', 'link': 'plugin:test:test_view'}]
        )

        # navigation name
        self.assertEqual(self.mixin.navigation_name, 'abcd1')
        self.assertEqual(self.nothing_mixin.navigation_name, '')

    def test_fail(self):
        """Test that wrong links fail."""
        with self.assertRaises(NotImplementedError):

            class NavigationCls(NavigationMixin, InvenTreePlugin):
                NAVIGATION = ['aa', 'aa']

            NavigationCls()


class APICallMixinTest(BaseMixinDefinition, TestCase):
    """Tests for APICallMixin."""

    MIXIN_HUMAN_NAME = 'API calls'
    MIXIN_NAME = 'api_call'
    MIXIN_ENABLE_CHECK = 'has_api_call'

    def setUp(self):
        """Setup for all tests."""

        class MixinCls(APICallMixin, SettingsMixin, InvenTreePlugin):
            NAME = 'Sample API Caller'

            SETTINGS = {
                'API_TOKEN': {'name': 'API Token', 'protected': True},
                'API_URL': {
                    'name': 'External URL',
                    'description': 'Where is your API located?',
                    'default': 'https://api.github.com',
                },
            }

            API_URL_SETTING = 'API_URL'
            API_TOKEN_SETTING = 'API_TOKEN'

            @property
            def api_url(self):
                """Override API URL for this test."""
                return 'https://api.github.com'

            def get_external_url(self, simple: bool = True):
                """Returns data from the sample endpoint."""
                return self.api_call('orgs/inventree', simple_response=simple)

        self.mixin = MixinCls()

        # If running in github workflow, make use of GITHUB_TOKEN
        if settings.TESTING:
            token = os.getenv('GITHUB_TOKEN', None)

            if token:
                self.mixin.set_setting('API_TOKEN', token)

        class WrongCLS(APICallMixin, InvenTreePlugin):
            pass

        self.mixin_wrong = WrongCLS()

        class WrongCLS2(APICallMixin, InvenTreePlugin):
            API_URL_SETTING = 'test'

        self.mixin_wrong2 = WrongCLS2()

    def test_base_setup(self):
        """Test that the base settings work."""
        # check init
        self.assertTrue(self.mixin.has_api_call)
        # api_url
        self.assertEqual('https://api.github.com', self.mixin.api_url)

        # api_headers
        headers = self.mixin.api_headers
        self.assertEqual(headers['Content-Type'], 'application/json')

    def test_args(self):
        """Test that building up args work."""
        # api_build_url_args
        # 1 arg
        result = self.mixin.api_build_url_args({'a': 'abc123'})
        self.assertEqual(result, '?a=abc123')
        # non string arg
        result = self.mixin.api_build_url_args({'a': 1})
        self.assertEqual(result, '?a=1')
        # more args
        result = self.mixin.api_build_url_args({'a': 'b', 'c': 42})
        self.assertEqual(result, '?a=b&c=42')
        # list args
        result = self.mixin.api_build_url_args({'a': 'b', 'c': ['d', 'efgh', 1337]})
        self.assertEqual(result, '?a=b&c=d,efgh,1337')

    def test_api_call(self):
        """Test that api calls work."""
        # api_call
        result = self.mixin.get_external_url()
        self.assertTrue(result)

        for key in ['login', 'email', 'name', 'twitter_username']:
            self.assertIn(key, result)

        # api_call without json conversion
        result = self.mixin.get_external_url(False)
        self.assertTrue(result)
        self.assertEqual(result.reason, 'OK')

        # api_call with post and data
        result = self.mixin.api_call(
            'https://reqres.in/api/users/',
            json={'name': 'morpheus', 'job': 'leader'},
            method='POST',
            endpoint_is_url=True,
        )

        self.assertTrue(result)
        self.assertEqual(result['name'], 'morpheus')

        # api_call with endpoint with leading slash
        result = self.mixin.api_call('/orgs/inventree', simple_response=False)
        self.assertTrue(result)
        self.assertEqual(result.reason, 'OK')

        # api_call with filter
        result = self.mixin.api_call(
            'repos/inventree/InvenTree/stargazers', url_args={'page': '2'}
        )
        self.assertTrue(result)

    def test_function_errors(self):
        """Test function errors."""
        # wrongly defined plugins should not load
        with self.assertRaises(MixinNotImplementedError):
            self.mixin_wrong.has_api_call()

        # cover wrong token setting
        with self.assertRaises(MixinNotImplementedError):
            self.mixin_wrong2.has_api_call()

        # Too many data arguments
        with self.assertRaises(ValueError):
            self.mixin.api_call(
                'https://reqres.in/api/users/', json={'a': 1}, data={'a': 1}
            )

        # Sending a request with a wrong data format should result in 40
        result = self.mixin.api_call(
            'https://reqres.in/api/users/',
            data={'name': 'morpheus', 'job': 'leader'},
            method='POST',
            endpoint_is_url=True,
            simple_response=False,
        )

        self.assertEqual(result.status_code, 400)
        self.assertIn('Bad Request', str(result.content))
