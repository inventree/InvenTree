# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from http import HTTPStatus
import json
from datetime import timedelta

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase
from .models import InvenTreeSetting, WebhookEndpoint, WebhookMessage, NotificationEntry
from .api import WebhookView

CONTENT_TYPE_JSON = 'application/json'


class SettingsTest(TestCase):
    """
    Tests for the 'settings' model
    """

    fixtures = [
        'settings',
    ]

    def setUp(self):

        user = get_user_model()

        self.user = user.objects.create_user('username', 'user@email.com', 'password')
        self.user.is_staff = True
        self.user.save()

        self.client.login(username='username', password='password')

    def test_settings_objects(self):

        # There should be two settings objects in the database
        settings = InvenTreeSetting.objects.all()

        self.assertTrue(settings.count() >= 2)

        instance_name = InvenTreeSetting.objects.get(pk=1)
        self.assertEqual(instance_name.key, 'INVENTREE_INSTANCE')
        self.assertEqual(instance_name.value, 'My very first InvenTree Instance')

        # Check object lookup (case insensitive)
        self.assertEqual(InvenTreeSetting.get_setting_object('iNvEnTrEE_inSTanCE').pk, 1)

    def test_settings_functions(self):
        """
        Test settings functions and properties
        """
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
        self.assertEqual(instance_obj.as_int(), 'InvenTree server')  # not an int -> return default

        # check as_bool
        self.assertEqual(report_test_obj.as_bool(), True)

        # check to_native_value
        self.assertEqual(stale_days.to_native_value(), 0)

    def test_allValues(self):
        """
        Make sure that the allValues functions returns correctly
        """
        # define testing settings

        # check a few keys
        result = InvenTreeSetting.allValues()
        self.assertIn('INVENTREE_INSTANCE', result)
        self.assertIn('PART_COPY_TESTS', result)
        self.assertIn('STOCK_OWNERSHIP_CONTROL', result)
        self.assertIn('SIGNUP_GROUP', result)

    def test_required_values(self):
        """
        - Ensure that every global setting has a name.
        - Ensure that every global setting has a description.
        """

        for key in InvenTreeSetting.SETTINGS.keys():

            setting = InvenTreeSetting.SETTINGS[key]

            name = setting.get('name', None)

            if name is None:
                raise ValueError(f'Missing GLOBAL_SETTING name for {key}')  # pragma: no cover

            description = setting.get('description', None)

            if description is None:
                raise ValueError(f'Missing GLOBAL_SETTING description for {key}')  # pragma: no cover

            if not key == key.upper():
                raise ValueError(f"SETTINGS key '{key}' is not uppercase")  # pragma: no cover

    def test_defaults(self):
        """
        Populate the settings with default values
        """

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


class SettingsApiTest(InvenTreeAPITestCase):

    def test_settings_api(self):
        # test setting with choice
        url = reverse('api-user-setting-list')
        self.get(url, expected_code=200)


class WebhookMessageTests(TestCase):
    def setUp(self):
        self.endpoint_def = WebhookEndpoint.objects.create()
        self.url = f'/api/webhook/{self.endpoint_def.endpoint_id}/'
        self.client = Client(enforce_csrf_checks=True)

    def test_bad_method(self):
        response = self.client.get(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_missing_token(self):
        response = self.client.post(
            self.url,
            content_type=CONTENT_TYPE_JSON,
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert (
            json.loads(response.content)['detail'] == WebhookView.model_class.MESSAGE_TOKEN_ERROR
        )

    def test_bad_token(self):
        response = self.client.post(
            self.url,
            content_type=CONTENT_TYPE_JSON,
            **{'HTTP_TOKEN': '1234567fghj'},
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert (json.loads(response.content)['detail'] == WebhookView.model_class.MESSAGE_TOKEN_ERROR)

    def test_bad_url(self):
        response = self.client.post(
            '/api/webhook/1234/',
            content_type=CONTENT_TYPE_JSON,
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_bad_json(self):
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


class NotificationTest(TestCase):

    def test_check_notification_entries(self):

        # Create some notification entries

        self.assertEqual(NotificationEntry.objects.count(), 0)

        NotificationEntry.notify('test.notification', 1)

        self.assertEqual(NotificationEntry.objects.count(), 1)

        delta = timedelta(days=1)

        self.assertFalse(NotificationEntry.check_recent('test.notification', 2, delta))
        self.assertFalse(NotificationEntry.check_recent('test.notification2', 1, delta))

        self.assertTrue(NotificationEntry.check_recent('test.notification', 1, delta))


class LoadingTest(TestCase):
    """
    Tests for the common config
    """

    def test_restart_flag(self):
        """
        Test that the restart flag is reset on start
        """

        import common.models
        from plugin import registry

        # set flag true
        common.models.InvenTreeSetting.set_setting('SERVER_RESTART_REQUIRED', False, None)

        # reload the app
        registry.reload_plugins()

        # now it should be false again
        self.assertFalse(common.models.InvenTreeSetting.get_setting('SERVER_RESTART_REQUIRED'))
