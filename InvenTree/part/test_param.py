# Tests for Part Parameters

import django.core.exceptions as django_exceptions
from django.test import TestCase, TransactionTestCase

from .models import (Part, PartCategory, PartCategoryParameterTemplate,
                     PartParameter, PartParameterTemplate)


class TestParams(TestCase):

    fixtures = [
        'location',
        'category',
        'part',
        'params'
    ]

    def test_str(self):

        t1 = PartParameterTemplate.objects.get(pk=1)
        self.assertEqual(str(t1), 'Length (mm)')

        p1 = PartParameter.objects.get(pk=1)
        self.assertEqual(str(p1), 'M2x4 LPHS : Length = 4mm')

        c1 = PartCategoryParameterTemplate.objects.get(pk=1)
        self.assertEqual(str(c1), 'Mechanical | Length | 2.8')

    def test_validate(self):

        n = PartParameterTemplate.objects.all().count()

        t1 = PartParameterTemplate(name='abcde', units='dd')
        t1.save()

        self.assertEqual(n + 1, PartParameterTemplate.objects.all().count())

        # Test that the case-insensitive name throws a ValidationError
        with self.assertRaises(django_exceptions.ValidationError):
            t3 = PartParameterTemplate(name='aBcde', units='dd')
            t3.full_clean()
            t3.save()  # pragma: no cover


class TestCategoryTemplates(TransactionTestCase):

    fixtures = [
        'location',
        'category',
        'part',
        'params'
    ]

    def test_validate(self):

        # Category templates
        n = PartCategoryParameterTemplate.objects.all().count()
        self.assertEqual(n, 2)

        category = PartCategory.objects.get(pk=8)

        t1 = PartParameterTemplate.objects.get(pk=2)
        c1 = PartCategoryParameterTemplate(category=category,
                                           parameter_template=t1,
                                           default_value='xyz')
        c1.save()

        n = PartCategoryParameterTemplate.objects.all().count()
        self.assertEqual(n, 3)

        # Get test part
        part = Part.objects.get(pk=1)

        # Get part parameters count
        n_param = part.get_parameters().count()

        add_category_templates = {
            'main': True,
            'parent': True,
        }
        # Save it with category parameters
        part.save(**{'add_category_templates': add_category_templates})

        # Check new part parameters count
        # Only 2 parameters should be added as one already existed with same template
        self.assertEqual(n_param + 2, part.get_parameters().count())
