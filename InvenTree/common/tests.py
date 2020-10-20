# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import Currency, InvenTreeSetting


class CurrencyTest(TestCase):
    """ Tests for Currency model """

    fixtures = [
        'currency',
    ]

    def test_currency(self):
        # Simple test for now (improve this later!)

        self.assertEqual(Currency.objects.count(), 2)


class SettingsTest(TestCase):
    """
    Tests for the 'settings' model
    """

    def setUp(self):

        User = get_user_model()
        
        self.user = User.objects.create_user('username', 'user@email.com', 'password')
        self.user.is_staff = True
        self.user.save()

        self.client.login(username='username', password='password')

    def test_defaults(self):
        """
        Populate the settings with default values
        """

        for key in InvenTreeSetting.DEFAULT_VALUES.keys():

            value = InvenTreeSetting.DEFAULT_VALUES[key]

            InvenTreeSetting.set_setting(key, value, self.user)

            self.assertEqual(str(value), InvenTreeSetting.get_setting(key))
