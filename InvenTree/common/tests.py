"""Tests for mechanisms in common."""

import json
from datetime import timedelta
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase
from InvenTree.helpers import InvenTreeTestCase, str2bool
from plugin import registry
from plugin.models import NotificationUserSetting, PluginConfig

from .api import WebhookView
from .models import (ColorTheme, InvenTreeSetting, InvenTreeUserSetting,
                     NotificationEntry, NotificationMessage, WebhookEndpoint,
                     WebhookMessage)

CONTENT_TYPE_JSON = 'application/json'


class SettingsTest(InvenTreeTestCase):
    """Tests for the 'settings' model."""

    fixtures = [
        'settings',
    ]

    def test_settings_objects(self):
        """Test fixture loading and lookup for settings."""
        # There should be two settings objects in the database
        settings = InvenTreeSetting.objects.all()

        self.assertTrue(settings.count() >= 2)

        instance_name = InvenTreeSetting.objects.get(pk=1)
        self.assertEqual(instance_name.key, 'INVENTREE_INSTANCE')
        self.assertEqual(instance_name.value, 'My very first InvenTree Instance')

        # Check object lookup (case insensitive)
        self.assertEqual(InvenTreeSetting.get_setting_object('iNvEnTrEE_inSTanCE').pk, 1)

    def test_settings_functions(self):
        """Test settings functions and properties."""
        # define settings to check
        instance_ref = 'INVENTREE_INSTANCE'
        instance_obj = InvenTreeSetting.get_setting_object(instance_ref)

        stale_ref = 'STOCK_STALE_DAYS'
        stale_days = InvenTreeSetting.get_setting_object(stale_ref)

        report_size_obj = InvenTreeSetting.get_setting_object('REPORT_DEFAULT_PAGE_SIZE')
        report_test_obj = InvenTreeSetting.get_setting_object('REPORT_ENABLE_TEST_REPORT')

        # check settings base fields
        self.assertEqual(instance_obj.name, 'Server Instance Name')
        self.assertEqual(instance_obj.get_setting_name(instance_ref), 'Server Instance Name')
        self.assertEqual(instance_obj.description, 'String descriptor for the server instance')
        self.assertEqual(instance_obj.get_setting_description(instance_ref), 'String descriptor for the server instance')

        # check units
        self.assertEqual(instance_obj.units, '')
        self.assertEqual(instance_obj.get_setting_units(instance_ref), '')
        self.assertEqual(instance_obj.get_setting_units(stale_ref), 'days')

        # check as_choice
        self.assertEqual(instance_obj.as_choice(), 'My very first InvenTree Instance')
        self.assertEqual(report_size_obj.as_choice(), 'A4')

        # check is_choice
        self.assertEqual(instance_obj.is_choice(), False)
        self.assertEqual(report_size_obj.is_choice(), True)

        # check setting_type
        self.assertEqual(instance_obj.setting_type(), 'string')
        self.assertEqual(report_test_obj.setting_type(), 'boolean')
        self.assertEqual(stale_days.setting_type(), 'integer')

        # check as_int
        self.assertEqual(stale_days.as_int(), 0)
        self.assertEqual(instance_obj.as_int(), 'InvenTree')  # not an int -> return default

        # check as_bool
        self.assertEqual(report_test_obj.as_bool(), True)

        # check to_native_value
        self.assertEqual(stale_days.to_native_value(), 0)

    def test_allValues(self):
        """Make sure that the allValues functions returns correctly."""
        # define testing settings

        # check a few keys
        result = InvenTreeSetting.allValues()
        self.assertIn('INVENTREE_INSTANCE', result)
        self.assertIn('PART_COPY_TESTS', result)
        self.assertIn('STOCK_OWNERSHIP_CONTROL', result)
        self.assertIn('SIGNUP_GROUP', result)

    def run_settings_check(self, key, setting):
        """Test that all settings are valid.

        - Ensure that a name is set and that it is translated
        - Ensure that a description is set
        - Ensure that every setting key is valid
        - Ensure that a validator is supplied
        """
        self.assertTrue(type(setting) is dict)

        name = setting.get('name', None)

        self.assertIsNotNone(name)
        self.assertIn('django.utils.functional.lazy', str(type(name)))

        description = setting.get('description', None)

        self.assertIsNotNone(description)
        self.assertIn('django.utils.functional.lazy', str(type(description)))

        if key != key.upper():
            raise ValueError(f"Setting key '{key}' is not uppercase")  # pragma: no cover

        # Check that only allowed keys are provided
        allowed_keys = [
            'name',
            'description',
            'default',
            'validator',
            'hidden',
            'choices',
            'units',
            'requires_restart',
        ]

        for k in setting.keys():
            self.assertIn(k, allowed_keys)

        # Check default value for boolean settings
        validator = setting.get('validator', None)

        if validator is bool:
            default = setting.get('default', None)

            # Default value *must* be supplied for boolean setting!
            self.assertIsNotNone(default)

            # Default value for boolean must itself be a boolean
            self.assertIn(default, [True, False])

    def test_setting_data(self):
        """Test for settings data.

        - Ensure that every setting has a name, which is translated
        - Ensure that every setting has a description, which is translated
        """
        for key, setting in InvenTreeSetting.SETTINGS.items():

            try:
                self.run_settings_check(key, setting)
            except Exception as exc:  # pragma: no cover
                print(f"run_settings_check failed for global setting '{key}'")
                raise exc

        for key, setting in InvenTreeUserSetting.SETTINGS.items():
            try:
                self.run_settings_check(key, setting)
            except Exception as exc:  # pragma: no cover
                print(f"run_settings_check failed for user setting '{key}'")
                raise exc

    def test_defaults(self):
        """Populate the settings with default values."""
        for key in InvenTreeSetting.SETTINGS.keys():

            value = InvenTreeSetting.get_setting_default(key)

            InvenTreeSetting.set_setting(key, value, self.user)

            self.assertEqual(value, InvenTreeSetting.get_setting(key))

            # Any fields marked as 'boolean' must have a default value specified
            setting = InvenTreeSetting.get_setting_object(key)

            if setting.is_bool():
                if setting.default_value in ['', None]:
                    raise ValueError(f'Default value for boolean setting {key} not provided')  # pragma: no cover

                if setting.default_value not in [True, False]:
                    raise ValueError(f'Non-boolean default value specified for {key}')  # pragma: no cover

    def test_global_setting_caching(self):
        """Test caching operations for the global settings class"""

        key = 'PART_NAME_FORMAT'

        cache_key = InvenTreeSetting.create_cache_key(key)
        self.assertEqual(cache_key, 'InvenTreeSetting:PART_NAME_FORMAT')

        self.assertIsNone(cache.get(cache_key))

        # First request should set cache
        val = InvenTreeSetting.get_setting(key)
        self.assertEqual(cache.get(cache_key).value, val)

        for val in ['A', '{{ part.IPN }}', 'C']:
            # Check that the cached value is updated whenever the setting is saved
            InvenTreeSetting.set_setting(key, val, None)
            self.assertEqual(cache.get(cache_key).value, val)
            self.assertEqual(InvenTreeSetting.get_setting(key), val)

    def test_user_setting_caching(self):
        """Test caching operation for the user settings class"""

        # Generate a number of new usesr
        for idx in range(5):
            get_user_model().objects.create(
                username=f"User_{idx}",
                password="hunter42",
                email="email@dot.com",
            )

        key = 'SEARCH_PREVIEW_RESULTS'

        # Check that the settings are correctly cached for each separate user
        for user in get_user_model().objects.all():
            print(user)
            setting = InvenTreeUserSetting.get_setting_object(key, user=user)
            cache_key = setting.cache_key
            self.assertEqual(cache_key, f"InvenTreeUserSetting:SEARCH_PREVIEW_RESULTS_user:{user.username}")
            InvenTreeUserSetting.set_setting(key, user.pk, None, user=user)
            self.assertIsNotNone(cache.get(cache_key))

        # Iterate through a second time, ensure the values have been cached correctly
        for user in get_user_model().objects.all():
            value = InvenTreeUserSetting.get_setting(key, user=user)
            self.assertEqual(value, user.pk)


class GlobalSettingsApiTest(InvenTreeAPITestCase):
    """Tests for the global settings API."""

    def test_global_settings_api_list(self):
        """Test list URL for global settings."""
        url = reverse('api-global-setting-list')

        # Read out each of the global settings value, to ensure they are instantiated in the database
        for key in InvenTreeSetting.SETTINGS:
            InvenTreeSetting.get_setting_object(key)

        response = self.get(url, expected_code=200)

        # Number of results should match the number of settings
        self.assertEqual(len(response.data), len(InvenTreeSetting.SETTINGS.keys()))

    def test_company_name(self):
        """Test a settings object lifecyle e2e."""
        setting = InvenTreeSetting.get_setting_object('INVENTREE_COMPANY_NAME')

        # Check default value
        self.assertEqual(setting.value, 'My company name')

        url = reverse('api-global-setting-detail', kwargs={'key': setting.key})

        # Test getting via the API
        for val in ['test', '123', 'My company nam3']:
            setting.value = val
            setting.save()

            response = self.get(url, expected_code=200)

            self.assertEqual(response.data['value'], val)

        # Test setting via the API
        for val in ['cat', 'hat', 'bat', 'mat']:
            response = self.patch(
                url,
                {
                    'value': val,
                },
                expected_code=200
            )

            self.assertEqual(response.data['value'], val)

            setting.refresh_from_db()
            self.assertEqual(setting.value, val)

    def test_api_detail(self):
        """Test that we can access the detail view for a setting based on the <key>."""
        # These keys are invalid, and should return 404
        for key in ["apple", "carrot", "dog"]:
            response = self.get(
                reverse('api-global-setting-detail', kwargs={'key': key}),
                expected_code=404,
            )

        key = 'INVENTREE_INSTANCE'
        url = reverse('api-global-setting-detail', kwargs={'key': key})

        InvenTreeSetting.objects.filter(key=key).delete()

        # Check that we can access a setting which has not previously been created
        self.assertFalse(InvenTreeSetting.objects.filter(key=key).exists())

        # Access via the API, and the default value should be received
        response = self.get(url, expected_code=200)

        self.assertEqual(response.data['value'], 'InvenTree')

        # Now, the object should have been created in the DB
        self.patch(
            url,
            {
                'value': 'My new title',
            },
            expected_code=200,
        )

        setting = InvenTreeSetting.objects.get(key=key)

        self.assertEqual(setting.value, 'My new title')

        # And retrieving via the API now returns the updated value
        response = self.get(url, expected_code=200)

        self.assertEqual(response.data['value'], 'My new title')


class UserSettingsApiTest(InvenTreeAPITestCase):
    """Tests for the user settings API."""

    def test_user_settings_api_list(self):
        """Test list URL for user settings."""
        url = reverse('api-user-setting-list')

        self.get(url, expected_code=200)

    def test_user_setting_invalid(self):
        """Test a user setting with an invalid key."""
        url = reverse('api-user-setting-detail', kwargs={'key': 'DONKEY'})

        self.get(url, expected_code=404)

    def test_user_setting_init(self):
        """Test we can retrieve a setting which has not yet been initialized."""
        key = 'HOMEPAGE_PART_LATEST'

        # Ensure it does not actually exist in the database
        self.assertFalse(InvenTreeUserSetting.objects.filter(key=key).exists())

        url = reverse('api-user-setting-detail', kwargs={'key': key})

        response = self.get(url, expected_code=200)

        self.assertEqual(response.data['value'], 'True')

        self.patch(url, {'value': 'False'}, expected_code=200)

        setting = InvenTreeUserSetting.objects.get(key=key, user=self.user)

        self.assertEqual(setting.value, 'False')
        self.assertEqual(setting.to_native_value(), False)

    def test_user_setting_boolean(self):
        """Test a boolean user setting value."""
        # Ensure we have a boolean setting available
        setting = InvenTreeUserSetting.get_setting_object(
            'SEARCH_PREVIEW_SHOW_PARTS',
            user=self.user
        )

        # Check default values
        self.assertEqual(setting.to_native_value(), True)

        # Fetch via API
        url = reverse('api-user-setting-detail', kwargs={'key': setting.key})

        response = self.get(url, expected_code=200)

        self.assertEqual(response.data['pk'], setting.pk)
        self.assertEqual(response.data['key'], 'SEARCH_PREVIEW_SHOW_PARTS')
        self.assertEqual(response.data['description'], 'Display parts in search preview window')
        self.assertEqual(response.data['type'], 'boolean')
        self.assertEqual(len(response.data['choices']), 0)
        self.assertTrue(str2bool(response.data['value']))

        # Assign some truthy values
        for v in ['true', True, 1, 'y', 'TRUE']:
            self.patch(
                url,
                {
                    'value': str(v),
                },
                expected_code=200,
            )

            response = self.get(url, expected_code=200)

            self.assertTrue(str2bool(response.data['value']))

        # Assign some falsey values
        for v in ['false', False, '0', 'n', 'FalSe']:
            self.patch(
                url,
                {
                    'value': str(v),
                },
                expected_code=200,
            )

            response = self.get(url, expected_code=200)

            self.assertFalse(str2bool(response.data['value']))

        # Assign some invalid values
        for v in ['x', '', 'invalid', None, '-1', 'abcde']:
            response = self.patch(
                url,
                {
                    'value': str(v),
                },
                expected_code=200
            )

            # Invalid values evaluate to False
            self.assertFalse(str2bool(response.data['value']))

    def test_user_setting_choice(self):
        """Test a user setting with choices."""
        setting = InvenTreeUserSetting.get_setting_object(
            'DATE_DISPLAY_FORMAT',
            user=self.user
        )

        url = reverse('api-user-setting-detail', kwargs={'key': setting.key})

        # Check default value
        self.assertEqual(setting.value, 'YYYY-MM-DD')

        # Check that a valid option can be assigned via the API
        for opt in ['YYYY-MM-DD', 'DD-MM-YYYY', 'MM/DD/YYYY']:

            self.patch(
                url,
                {
                    'value': opt,
                },
                expected_code=200,
            )

            setting.refresh_from_db()
            self.assertEqual(setting.value, opt)

        # Send an invalid option
        for opt in ['cat', 'dog', 12345]:

            response = self.patch(
                url,
                {
                    'value': opt,
                },
                expected_code=400,
            )

            self.assertIn('Chosen value is not a valid option', str(response.data))

    def test_user_setting_integer(self):
        """Test a integer user setting value."""
        setting = InvenTreeUserSetting.get_setting_object(
            'SEARCH_PREVIEW_RESULTS',
            user=self.user
        )

        url = reverse('api-user-setting-detail', kwargs={'key': setting.key})

        # Check default value for this setting
        self.assertEqual(setting.value, 10)

        for v in [1, 9, 99]:
            setting.value = v
            setting.save()

            response = self.get(url)

            self.assertEqual(response.data['value'], str(v))

        # Set valid options via the api
        for v in [5, 15, 25]:
            self.patch(
                url,
                {
                    'value': v,
                },
                expected_code=200,
            )

            setting.refresh_from_db()
            self.assertEqual(setting.to_native_value(), v)

        # Set invalid options via the API
        # Note that this particular setting has a MinValueValidator(1) associated with it
        for v in [0, -1, -5]:

            response = self.patch(
                url,
                {
                    'value': v,
                },
                expected_code=400,
            )


class NotificationUserSettingsApiTest(InvenTreeAPITestCase):
    """Tests for the notification user settings API."""

    def test_api_list(self):
        """Test list URL."""
        url = reverse('api-notifcation-setting-list')

        self.get(url, expected_code=200)

    def test_setting(self):
        """Test the string name for NotificationUserSetting."""
        test_setting = NotificationUserSetting.get_setting_object('NOTIFICATION_METHOD_MAIL', user=self.user)
        self.assertEqual(str(test_setting), 'NOTIFICATION_METHOD_MAIL (for testuser): ')


class PluginSettingsApiTest(InvenTreeAPITestCase):
    """Tests for the plugin settings API."""

    def test_plugin_list(self):
        """List installed plugins via API."""
        url = reverse('api-plugin-list')

        # Simple request
        self.get(url, expected_code=200)

        # Request with filter
        self.get(url, expected_code=200, data={'mixin': 'settings'})

    def test_api_list(self):
        """Test list URL."""
        url = reverse('api-plugin-setting-list')

        self.get(url, expected_code=200)

    def test_valid_plugin_slug(self):
        """Test that an valid plugin slug runs through."""
        # load plugin configs
        fixtures = PluginConfig.objects.all()
        if not fixtures:
            registry.reload_plugins()
            fixtures = PluginConfig.objects.all()

        # get data
        url = reverse('api-plugin-setting-detail', kwargs={'plugin': 'sample', 'key': 'API_KEY'})
        response = self.get(url, expected_code=200)

        # check the right setting came through
        self.assertTrue(response.data['key'], 'API_KEY')
        self.assertTrue(response.data['plugin'], 'sample')
        self.assertTrue(response.data['type'], 'string')
        self.assertTrue(response.data['description'], 'Key required for accessing external API')

        # Failure mode tests

        # Non - exsistant plugin
        url = reverse('api-plugin-setting-detail', kwargs={'plugin': 'doesnotexist', 'key': 'doesnotmatter'})
        response = self.get(url, expected_code=404)
        self.assertIn("Plugin 'doesnotexist' not installed", str(response.data))

        # Wrong key
        url = reverse('api-plugin-setting-detail', kwargs={'plugin': 'sample', 'key': 'doesnotexsist'})
        response = self.get(url, expected_code=404)
        self.assertIn("Plugin 'sample' has no setting matching 'doesnotexsist'", str(response.data))

    def test_invalid_setting_key(self):
        """Test that an invalid setting key returns a 404."""
        ...

    def test_uninitialized_setting(self):
        """Test that requesting an uninitialized setting creates the setting."""
        ...


class WebhookMessageTests(TestCase):
    """Tests for webhooks."""

    def setUp(self):
        """Setup for all tests."""
        self.endpoint_def = WebhookEndpoint.objects.create()
        self.url = f'/api/webhook/{self.endpoint_def.endpoint_id}/'
        self.client = Client(enforce_csrf_checks=True)

    def test_bad_method(self):
        """Test that a wrong HTTP method does not work."""
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_missing_token(self):
        """Tests that token checks work."""
        response = self.client.post(
            self.url,
            content_type=CONTENT_TYPE_JSON,
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert (
            json.loads(response.content)['detail'] == WebhookView.model_class.MESSAGE_TOKEN_ERROR
        )

    def test_bad_token(self):
        """Test that a wrong token is not working."""
        response = self.client.post(
            self.url,
            content_type=CONTENT_TYPE_JSON,
            **{'HTTP_TOKEN': '1234567fghj'},
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert (json.loads(response.content)['detail'] == WebhookView.model_class.MESSAGE_TOKEN_ERROR)

    def test_bad_url(self):
        """Test that a wrongly formed url is not working."""
        response = self.client.post(
            '/api/webhook/1234/',
            content_type=CONTENT_TYPE_JSON,
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_bad_json(self):
        """Test that malformed JSON is not accepted."""
        response = self.client.post(
            self.url,
            data="{'this': 123}",
            content_type=CONTENT_TYPE_JSON,
            **{'HTTP_TOKEN': str(self.endpoint_def.token)},
        )

        assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
        assert (
            json.loads(response.content)['detail'] == 'Expecting property name enclosed in double quotes'
        )

    def test_success_no_token_check(self):
        """Test that a endpoint without a token set does not require one."""
        # delete token
        self.endpoint_def.token = ''
        self.endpoint_def.save()

        # check
        response = self.client.post(
            self.url,
            content_type=CONTENT_TYPE_JSON,
        )

        assert response.status_code == HTTPStatus.OK
        assert str(response.content, 'utf-8') == WebhookView.model_class.MESSAGE_OK

    def test_bad_hmac(self):
        """Test that a malformed HMAC does not pass."""
        # delete token
        self.endpoint_def.token = ''
        self.endpoint_def.secret = '123abc'
        self.endpoint_def.save()

        # check
        response = self.client.post(
            self.url,
            content_type=CONTENT_TYPE_JSON,
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert (json.loads(response.content)['detail'] == WebhookView.model_class.MESSAGE_TOKEN_ERROR)

    def test_success_hmac(self):
        """Test with a valid HMAC provided."""
        # delete token
        self.endpoint_def.token = ''
        self.endpoint_def.secret = '123abc'
        self.endpoint_def.save()

        # check
        response = self.client.post(
            self.url,
            content_type=CONTENT_TYPE_JSON,
            **{'HTTP_TOKEN': str('68MXtc/OiXdA5e2Nq9hATEVrZFpLb3Zb0oau7n8s31I=')},
        )

        assert response.status_code == HTTPStatus.OK
        assert str(response.content, 'utf-8') == WebhookView.model_class.MESSAGE_OK

    def test_success(self):
        """Test full e2e webhook call.

        The message should go through and save the json payload.
        """
        response = self.client.post(
            self.url,
            data={"this": "is a message"},
            content_type=CONTENT_TYPE_JSON,
            **{'HTTP_TOKEN': str(self.endpoint_def.token)},
        )

        assert response.status_code == HTTPStatus.OK
        assert str(response.content, 'utf-8') == WebhookView.model_class.MESSAGE_OK
        message = WebhookMessage.objects.get()
        assert message.body == {"this": "is a message"}


class NotificationTest(InvenTreeAPITestCase):
    """Tests for NotificationEntriy."""

    fixtures = [
        'users',
    ]

    def test_check_notification_entries(self):
        """Test that notification entries can be created."""
        # Create some notification entries

        self.assertEqual(NotificationEntry.objects.count(), 0)

        NotificationEntry.notify('test.notification', 1)

        self.assertEqual(NotificationEntry.objects.count(), 1)

        delta = timedelta(days=1)

        self.assertFalse(NotificationEntry.check_recent('test.notification', 2, delta))
        self.assertFalse(NotificationEntry.check_recent('test.notification2', 1, delta))

        self.assertTrue(NotificationEntry.check_recent('test.notification', 1, delta))

    def test_api_list(self):
        """Test list URL."""

        url = reverse('api-notifications-list')

        self.get(url, expected_code=200)

        # Test the OPTIONS endpoint for the 'api-notification-list'
        # Ref: https://github.com/inventree/InvenTree/pull/3154
        response = self.options(url)

        self.assertIn('DELETE', response.data['actions'])
        self.assertIn('GET', response.data['actions'])
        self.assertNotIn('POST', response.data['actions'])

        self.assertEqual(response.data['description'], 'List view for all notifications of the current user.')

        # POST action should fail (not allowed)
        response = self.post(url, {}, expected_code=405)

    def test_bulk_delete(self):
        """Tests for bulk deletion of user notifications"""

        from error_report.models import Error

        # Create some notification messages by throwing errors
        for _ii in range(10):
            Error.objects.create()

        # Check that messsages have been created
        messages = NotificationMessage.objects.all()

        # As there are three staff users (including the 'test' user) we expect 30 notifications
        self.assertEqual(messages.count(), 30)

        # Only 10 messages related to *this* user
        my_notifications = messages.filter(user=self.user)
        self.assertEqual(my_notifications.count(), 10)

        # Get notification via the API
        url = reverse('api-notifications-list')
        response = self.get(url, {}, expected_code=200)
        self.assertEqual(len(response.data), 10)

        # Mark some as read
        for ntf in my_notifications[0:3]:
            ntf.read = True
            ntf.save()

        # Read out via API again
        response = self.get(
            url,
            {
                'read': True,
            },
            expected_code=200
        )

        # Check validity of returned data
        self.assertEqual(len(response.data), 3)
        for ntf in response.data:
            self.assertTrue(ntf['read'])

        # Now, let's bulk delete all 'unread' notifications via the API,
        # but only associated with the logged in user
        response = self.delete(
            url,
            {
                'filters': {
                    'read': False,
                }
            },
            expected_code=204,
        )

        # Only 7 notifications should have been deleted,
        # as the notifications associated with other users must remain untouched
        self.assertEqual(NotificationMessage.objects.count(), 23)
        self.assertEqual(NotificationMessage.objects.filter(user=self.user).count(), 3)


class LoadingTest(TestCase):
    """Tests for the common config."""

    def test_restart_flag(self):
        """Test that the restart flag is reset on start."""
        import common.models
        from plugin import registry

        # set flag true
        common.models.InvenTreeSetting.set_setting('SERVER_RESTART_REQUIRED', False, None)

        # reload the app
        registry.reload_plugins()

        # now it should be false again
        self.assertFalse(common.models.InvenTreeSetting.get_setting('SERVER_RESTART_REQUIRED'))


class ColorThemeTest(TestCase):
    """Tests for ColorTheme."""

    def test_choices(self):
        """Test that default choices are returned."""
        result = ColorTheme.get_color_themes_choices()

        # skip
        if not result:
            return
        self.assertIn(('default', 'Default'), result)

    def test_valid_choice(self):
        """Check that is_valid_choice works correctly."""
        result = ColorTheme.get_color_themes_choices()

        # skip
        if not result:
            return

        # check wrong reference
        self.assertFalse(ColorTheme.is_valid_choice('abcdd'))

        # create themes
        aa = ColorTheme.objects.create(user='aa', name='testname')
        ab = ColorTheme.objects.create(user='ab', name='darker')

        # check valid theme
        self.assertFalse(ColorTheme.is_valid_choice(aa))
        self.assertTrue(ColorTheme.is_valid_choice(ab))
