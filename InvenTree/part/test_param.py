"""Various unit tests for Part Parameters"""

import django.core.exceptions as django_exceptions
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase
from InvenTree.status_codes import PartParameterTypeCode

from .models import (Part, PartCategory, PartCategoryParameterTemplate,
                     PartParameter, PartParameterTemplate)


class TestParams(TestCase):
    """Unit test class for testing the PartParameter model"""

    fixtures = [
        'location',
        'category',
        'part',
        'params'
    ]

    def test_str(self):
        """Test the str representation of the PartParameterTemplate model"""
        t1 = PartParameterTemplate.objects.get(pk=1)
        self.assertEqual(str(t1), 'Length (mm)')

        p1 = PartParameter.objects.get(pk=1)
        self.assertEqual(str(p1), 'M2x4 LPHS : Length = 4mm')

        c1 = PartCategoryParameterTemplate.objects.get(pk=1)
        self.assertEqual(str(c1), 'Mechanical | Length | 2.8')

    def test_validate(self):
        """Test validation for part templates"""
        n = PartParameterTemplate.objects.all().count()

        t1 = PartParameterTemplate(name='abcde', units='dd')
        t1.save()

        self.assertEqual(n + 1, PartParameterTemplate.objects.all().count())

        # Test that the case-insensitive name throws a ValidationError
        with self.assertRaises(django_exceptions.ValidationError):
            t3 = PartParameterTemplate(name='aBcde', units='dd')
            t3.full_clean()
            t3.save()  # pragma: no cover

    def test_metadata(self):
        """Unit tests for the metadata field."""
        for model in [PartParameterTemplate]:
            p = model.objects.first()

            self.assertIsNone(p.get_metadata('test'))
            self.assertEqual(p.get_metadata('test', backup_value=123), 123)

            # Test update via the set_metadata() method
            p.set_metadata('test', 3)
            self.assertEqual(p.get_metadata('test'), 3)

            for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
                p.set_metadata(k, k)

            self.assertEqual(len(p.metadata.keys()), 4)


class TestCategoryTemplates(TransactionTestCase):
    """Test class for PartCategoryParameterTemplate model"""

    fixtures = [
        'location',
        'category',
        'part',
        'params'
    ]

    def test_validate(self):
        """Test that category templates are correctly applied to Part instances"""
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


class ParameterValidationTest(TestCase):
    """Unit tests for parameter validation"""

    fixtures = [
        'location',
        'category',
        'part',
        'params'
    ]

    def test_param_validation(self):
        """Unit tests for parameter validation based on template type"""

        # Create some specific parameter templates
        tmp_int = PartParameterTemplate.objects.create(
            name='Test Integer',
            description='An integer parameter template',
            param_type=PartParameterTypeCode.INTEGER,
        )

        tmp_flt = PartParameterTemplate.objects.create(
            name='Test Float',
            description='A float parameter template',
            param_type=PartParameterTypeCode.FLOAT,
        )

        tmp_reg = PartParameterTemplate.objects.create(
            name='Test Regex',
            description='A regex parameter template',
            param_type=PartParameterTypeCode.REGEX,
            validator='^num[0-9]+$',
        )

        tmp_opt = PartParameterTemplate.objects.create(
            name='Test Options',
            description='An options parameter template',
            param_type=PartParameterTypeCode.CHOICE,
            validator='red,green,blue',
        )

        # Construct a set of pass / fail values based on each template type
        test_values = {
            tmp_int: {
                'pass': [-100, 2, 0, '23'],
                'fail': ['a', 'b', '1.2'],
            },
            tmp_flt: {
                'pass': [1, -2, 1.0, 2.0, '34'],
                'fail': ['a', 'b', '-1.x', 'g.4'],
            },
            tmp_reg: {
                'pass': ['num1', 'num2', 'num344'],
                'fail': ['a', '1.0', 'num', 'nun1'],
            },
            tmp_opt: {
                'pass': ['red', 'green', 'blue'],
                'fail': ['a', 'b', 'c', 'd', 'e'],
            }
        }

        prt = Part.objects.get(pk=3)

        # Run the tests!
        for template, data in test_values.items():
            for value in data['pass']:

                param = PartParameter(
                    template=template,
                    part=prt,
                    data=value
                )

                param.clean()

            for value in data['fail']:

                param = PartParameter(
                    template=template,
                    part=prt,
                    data=value
                )

                with self.assertRaises(django_exceptions.ValidationError):
                    param.clean()


class PartParameterTest(InvenTreeAPITestCase):
    """Tests for the ParParameter API."""
    superuser = True

    fixtures = [
        'category',
        'part',
        'location',
        'params',
    ]

    def test_list_params(self):
        """Test for listing part parameters."""
        url = reverse('api-part-parameter-list')

        response = self.get(url)

        self.assertEqual(len(response.data), 7)

        # Filter by part
        response = self.get(
            url,
            {
                'part': 3,
            }
        )

        self.assertEqual(len(response.data), 3)

        # Filter by template
        response = self.get(
            url,
            {
                'template': 1,
            }
        )

        self.assertEqual(len(response.data), 4)

    def test_create_param(self):
        """Test that we can create a param via the API."""
        url = reverse('api-part-parameter-list')

        response = self.post(
            url,
            {
                'part': '2',
                'template': '3',
                'data': 70
            }
        )

        self.assertEqual(response.status_code, 201)

        response = self.get(url)

        self.assertEqual(len(response.data), 8)

    def test_param_detail(self):
        """Tests for the PartParameter detail endpoint."""
        url = reverse('api-part-parameter-detail', kwargs={'pk': 5})

        response = self.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.data

        self.assertEqual(data['pk'], 5)
        self.assertEqual(data['part'], 3)
        self.assertEqual(data['data'], '12')

        # PATCH data back in
        response = self.patch(url, {'data': '15'})

        self.assertEqual(response.status_code, 200)

        # Check that the data changed!
        response = self.get(url)

        data = response.data

        self.assertEqual(data['data'], '15')
