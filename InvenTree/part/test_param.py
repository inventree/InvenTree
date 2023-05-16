"""Various unit tests for Part Parameters"""

import django.core.exceptions as django_exceptions
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase

from .models import (PartCategory, PartCategoryParameterTemplate,
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


class ParameterTests(TestCase):
    """Unit tests for parameter validation"""

    def test_unit_validation(self):
        """Test validation of 'units' field for PartParameterTemplate"""

        # Test that valid units pass
        for unit in ['', 'mm', 'A', 'm^2', 'Pa', 'V', 'C', 'F', 'uF', 'mF', 'millifarad']:
            tmp = PartParameterTemplate(name='test', units=unit)
            tmp.full_clean()

        # Test that invalid units fail
        for unit in ['mmmmm', '-', 'x']:
            tmp = PartParameterTemplate(name='test', units=unit)
            with self.assertRaises(django_exceptions.ValidationError):
                tmp.full_clean()


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
