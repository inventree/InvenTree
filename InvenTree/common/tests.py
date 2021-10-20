# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from http import HTTPStatus
import json

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from .models import InvenTreeSetting, WebhookEndpoint, WebhookMessage
from .api import WebhookView


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

    def test_required_values(self):
        """
        - Ensure that every global setting has a name.
        - Ensure that every global setting has a description.
        """

        for key in InvenTreeSetting.GLOBAL_SETTINGS.keys():

            setting = InvenTreeSetting.GLOBAL_SETTINGS[key]

            name = setting.get('name', None)

            if name is None:
                raise ValueError(f'Missing GLOBAL_SETTING name for {key}')

            description = setting.get('description', None)

            if description is None:
                raise ValueError(f'Missing GLOBAL_SETTING description for {key}')

            if not key == key.upper():
                raise ValueError(f"GLOBAL_SETTINGS key '{key}' is not uppercase")

    def test_defaults(self):
        """
        Populate the settings with default values
        """

        for key in InvenTreeSetting.GLOBAL_SETTINGS.keys():

            value = InvenTreeSetting.get_setting_default(key)

            InvenTreeSetting.set_setting(key, value, self.user)

            self.assertEqual(value, InvenTreeSetting.get_setting(key))

            # Any fields marked as 'boolean' must have a default value specified
            setting = InvenTreeSetting.get_setting_object(key)

            if setting.is_bool():
                if setting.default_value in ['', None]:
                    raise ValueError(f'Default value for boolean setting {key} not provided')

                if setting.default_value not in [True, False]:
                    raise ValueError(f'Non-boolean default value specified for {key}')


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
            content_type='application/json',
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert (
            json.loads(response.content)['detail'] == WebhookView.model_class.MESSAGE_TOKEN_ERROR
        )

    def test_bad_token(self):
        response = self.client.post(
            self.url,
            content_type='application/json',
            **{'HTTP_TOKEN': '1234567fghj'},
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert (json.loads(response.content)['detail'] == WebhookView.model_class.MESSAGE_TOKEN_ERROR)

    def test_bad_url(self):
        response = self.client.post(
            '/api/webhook/1234/',
            content_type='application/json',
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_bad_json(self):
        response = self.client.post(
            self.url,
            data="{'this': 123}",
            content_type='application/json',
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
            content_type='application/json',
        )

        assert response.status_code == HTTPStatus.OK
        assert response.content == WebhookView.model_class.MESSAGE_OK

    def test_bad_hmac(self):
        # delete token
        self.endpoint_def.token = ''
        self.endpoint_def.secret = '123abc'
        self.endpoint_def.save()

        # check
        response = self.client.post(
            self.url,
            content_type='application/json',
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
            content_type='application/json',
            **{'HTTP_TOKEN': str('68MXtc/OiXdA5e2Nq9hATEVrZFpLb3Zb0oau7n8s31I=')},
        )

        assert response.status_code == HTTPStatus.OK
        assert json.loads(response.content)['message'] == WebhookView.model_class.MESSAGE_OK

    def test_success(self):
        response = self.client.post(
            self.url,
            data={"this": "is a message"},
            content_type='application/json',
            **{'HTTP_TOKEN': str(self.endpoint_def.token)},
        )

        assert response.status_code == HTTPStatus.OK
        assert json.loads(response.content)['message'] == WebhookView.model_class.MESSAGE_OK
        message = WebhookMessage.objects.get()
        assert message.body == {"this": "is a message"}
