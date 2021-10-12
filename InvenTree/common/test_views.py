"""
Unit tests for the views associated with the 'common' app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from common.models import InvenTreeSetting


class SettingsViewTest(TestCase):
    """
    Tests for the settings management views
    """

    fixtures = [
        'settings',
    ]

    def setUp(self):
        super().setUp()

        # Create a user (required to access the views / forms)
        self.user = get_user_model().objects.create_user(
            username='username',
            email='me@email.com',
            password='password',
        )

        self.client.login(username='username', password='password')

    def get_url(self, pk):
        return reverse('setting-edit', args=(pk,))

    def get_setting(self, title):

        return InvenTreeSetting.get_setting_object(title)

    def get(self, url, status=200):

        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, status)

        data = json.loads(response.content)

        return response, data

    def post(self, url, data, valid=None):

        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        json_data = json.loads(response.content)

        # If a particular status code is required
        if valid is not None:
            if valid:
                self.assertEqual(json_data['form_valid'], True)
            else:
                self.assertEqual(json_data['form_valid'], False)

        form_errors = json.loads(json_data['form_errors'])

        return json_data, form_errors

    def test_instance_name(self):
        """
        Test that we can get the settings view for particular setting objects.
        """

        # Start with something basic - load the settings view for INVENTREE_INSTANCE
        setting = self.get_setting('INVENTREE_INSTANCE')

        self.assertIsNotNone(setting)
        self.assertEqual(setting.value, 'My very first InvenTree Instance')

        url = self.get_url(setting.pk)

        self.get(url)

        new_name = 'A new instance name!'

        # Change the instance name via the form
        data, errors = self.post(url, {'value': new_name}, valid=True)

        name = InvenTreeSetting.get_setting('INVENTREE_INSTANCE')

        self.assertEqual(name, new_name)

    def test_choices(self):
        """
        Tests for a setting which has choices
        """

        setting = InvenTreeSetting.get_setting_object('PURCHASEORDER_REFERENCE_PREFIX')

        # Default value!
        self.assertEqual(setting.value, 'PO')

        url = self.get_url(setting.pk)

        # Try posting an invalid currency option
        data, errors = self.post(url, {'value': 'Purchase Order'}, valid=True)

    def test_binary_values(self):
        """
        Test for binary value
        """

        setting = InvenTreeSetting.get_setting_object('PART_COMPONENT')

        self.assertTrue(setting.as_bool())

        url = self.get_url(setting.pk)

        setting.value = True
        setting.save()

        # Try posting some invalid values
        # The value should be "cleaned" and stay the same
        for value in ['', 'abc', 'cat', 'TRUETRUETRUE']:
            self.post(url, {'value': value}, valid=True)

        # Try posting some valid (True) values
        for value in [True, 'True', '1', 'yes']:
            self.post(url, {'value': value}, valid=True)
            self.assertTrue(InvenTreeSetting.get_setting('PART_COMPONENT'))

        # Try posting some valid (False) values
        for value in [False, 'False']:
            self.post(url, {'value': value}, valid=True)
            self.assertFalse(InvenTreeSetting.get_setting('PART_COMPONENT'))

    def test_part_name_format(self):
        """
        Try posting some valid and invalid name formats for PART_NAME_FORMAT
        """
        setting = InvenTreeSetting.get_setting_object('PART_NAME_FORMAT')

        # test default value
        self.assertEqual(setting.value, "{{ part.IPN if part.IPN }} {{ '|' if part.IPN }} {{ part.name }} "
                                        "{{ '|' if part.revision }} {{ part.revision }}")

        url = self.get_url(setting.pk)

        # Try posting an invalid part name  format
        invalid_values = ['{{asset.IPN}}', '{{part}}', '{{"|"}}']
        for invalid_value in invalid_values:
            self.post(url, {'value': invalid_value}, valid=False)

        # try posting valid value
        new_format = "{{ part.name if part.name }} {{ ' with revision ' if part.revision }} {{ part.revision }}"
        self.post(url, {'value': new_format}, valid=True)

