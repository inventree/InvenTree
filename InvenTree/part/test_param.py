# Tests for Part Parameters

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
import django.core.exceptions as django_exceptions

from .models import PartParameter, PartParameterTemplate


class TestParams(TestCase):

    fixtures = [
        'location',
        'category',
        'part',
        'params'
    ]

    def test_str(self):

        t1 = PartParameterTemplate.objects.get(pk=1)
        self.assertEquals(str(t1), 'Length (mm)')

        p1 = PartParameter.objects.get(pk=1)
        self.assertEqual(str(p1), "M2x4 LPHS : Length = 4mm")

    def test_validate(self):
        
        n = PartParameterTemplate.objects.all().count()

        t1 = PartParameterTemplate(name='abcde', units='dd')
        t1.save()

        self.assertEqual(n + 1, PartParameterTemplate.objects.all().count())

        # Test that the case-insensitive name throws a ValidationError
        with self.assertRaises(django_exceptions.ValidationError):
            t3 = PartParameterTemplate(name='aBcde', units='dd')
            t3.full_clean()
            t3.save()
