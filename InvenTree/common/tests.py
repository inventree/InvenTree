# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from .models import Currency


class CurrencyTest(TestCase):
    """ Tests for Currency model """

    fixtures = [
        'currency',
    ]

    def test_currency(self):
        # Simple test for now (improve this later!)

        self.assertEqual(Currency.objects.count(), 2)
