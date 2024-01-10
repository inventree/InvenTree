"""Various unit tests for Part Parameters."""

import django.core.exceptions as django_exceptions
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from common.models import InvenTreeSetting

from InvenTree.unit_test import InvenTreeAPITestCase

from .models import (
    Part,
    PartCategory,
    PartCategoryParameterTemplate,
    PartParameter,
    PartParameterTemplate,
)


class TestParams(TestCase):
    """Unit test class for testing the PartParameter model."""

    fixtures = ['location', 'category', 'part', 'params']

    def test_str(self):
        """Test the str representation of the PartParameterTemplate model."""
        t1 = PartParameterTemplate.objects.get(pk=1)
        self.assertEqual(str(t1), 'Length (mm)')

        p1 = PartParameter.objects.get(pk=1)
        self.assertEqual(str(p1), 'M2x4 LPHS : Length = 4 (mm)')

        c1 = PartCategoryParameterTemplate.objects.get(pk=1)
        self.assertEqual(str(c1), 'Mechanical | Length | 2.8')

    def test_validate(self):
        """Test validation for part templates."""
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

    def test_get_parameter(self):
        """Test the Part.get_parameter method."""
        prt = Part.objects.get(pk=3)

        # Check that we can get a parameter by name
        for name in ['Length', 'Width', 'Thickness']:
            param = prt.get_parameter(name)
            self.assertEqual(param.template.name, name)

        # Check that an incorrect name returns None
        param = prt.get_parameter('Not a parameter')
        self.assertIsNone(param)


class TestCategoryTemplates(TransactionTestCase):
    """Test class for PartCategoryParameterTemplate model."""

    fixtures = ['location', 'category', 'part', 'params']

    def test_validate(self):
        """Test that category templates are correctly applied to Part instances."""
        # Category templates
        n = PartCategoryParameterTemplate.objects.all().count()
        self.assertEqual(n, 2)

        category = PartCategory.objects.get(pk=8)

        t1 = PartParameterTemplate.objects.get(pk=2)
        c1 = PartCategoryParameterTemplate(
            category=category, parameter_template=t1, default_value='xyz'
        )
        c1.save()

        n = PartCategoryParameterTemplate.objects.all().count()
        self.assertEqual(n, 3)


class ParameterTests(TestCase):
    """Unit tests for parameter validation."""

    fixtures = ['location', 'category', 'part', 'params']

    def test_choice_validation(self):
        """Test that parameter choices are correctly validated."""
        template = PartParameterTemplate.objects.create(
            name='My Template',
            description='A template with choices',
            choices='red, blue, green',
        )

        pass_values = ['red', 'blue', 'green']
        fail_values = ['rod', 'bleu', 'grene']

        part = Part.objects.all().first()

        for value in pass_values:
            param = PartParameter(part=part, template=template, data=value)
            param.full_clean()

        for value in fail_values:
            param = PartParameter(part=part, template=template, data=value)
            with self.assertRaises(django_exceptions.ValidationError):
                param.full_clean()

    def test_unit_validation(self):
        """Test validation of 'units' field for PartParameterTemplate."""
        # Test that valid units pass
        for unit in [
            None,
            '',
            '%',
            'mm',
            'A',
            'm^2',
            'Pa',
            'V',
            'C',
            'F',
            'uF',
            'mF',
            'millifarad',
        ]:
            tmp = PartParameterTemplate(name='test', units=unit)
            tmp.full_clean()

        # Test that invalid units fail
        for unit in ['mmmmm', '-', 'x', int]:
            tmp = PartParameterTemplate(name='test', units=unit)
            with self.assertRaises(django_exceptions.ValidationError):
                tmp.full_clean()

    def test_param_unit_validation(self):
        """Test that parameters are correctly validated against template units."""
        template = PartParameterTemplate.objects.create(name='My Template', units='m')

        prt = Part.objects.get(pk=1)

        # Test that valid parameters pass
        for value in [
            '1',
            '1m',
            'm',
            '-4m',
            -2,
            '2.032mm',
            '99km',
            '-12 mile',
            'foot',
            '3 yards',
        ]:
            param = PartParameter(part=prt, template=template, data=value)
            param.full_clean()

        # Test that percent unit is working
        template2 = PartParameterTemplate.objects.create(
            name='My Template 2', units='%'
        )
        for value in ['1', '1%', '1 percent']:
            param = PartParameter(part=prt, template=template2, data=value)
            param.full_clean()

        bad_values = ['3 Amps', '-3 zogs', '3.14F']

        # Disable enforcing of part parameter units
        InvenTreeSetting.set_setting(
            'PART_PARAMETER_ENFORCE_UNITS', False, change_user=None
        )

        # Invalid units also pass, but will be converted to the template units
        for value in bad_values:
            param = PartParameter(part=prt, template=template, data=value)
            param.full_clean()

        # Enable enforcing of part parameter units
        InvenTreeSetting.set_setting(
            'PART_PARAMETER_ENFORCE_UNITS', True, change_user=None
        )

        for value in bad_values:
            param = PartParameter(part=prt, template=template, data=value)
            with self.assertRaises(django_exceptions.ValidationError):
                param.full_clean()

    def test_param_unit_conversion(self):
        """Test that parameters are correctly converted to template units."""
        template = PartParameterTemplate.objects.create(name='My Template', units='m')

        tests = {
            '1': 1.0,
            '-1': -1.0,
            '23m': 23.0,
            '-89mm': -0.089,
            '100 foot': 30.48,
            '-17 yards': -15.54,
        }

        prt = Part.objects.get(pk=1)
        param = PartParameter(part=prt, template=template, data='1')

        for value, expected in tests.items():
            param.data = value
            param.calculate_numeric_value()
            self.assertAlmostEqual(param.data_numeric, expected, places=2)


class PartParameterTest(InvenTreeAPITestCase):
    """Tests for the ParParameter API."""

    superuser = True

    fixtures = ['category', 'part', 'location', 'params']

    def test_list_params(self):
        """Test for listing part parameters."""
        url = reverse('api-part-parameter-list')

        response = self.get(url)

        self.assertEqual(len(response.data), 7)

        # Filter by part
        response = self.get(url, {'part': 3})

        self.assertEqual(len(response.data), 3)

        # Filter by template
        response = self.get(url, {'template': 1})

        self.assertEqual(len(response.data), 4)

    def test_param_template_validation(self):
        """Test that part parameter template validation routines work correctly."""
        # Checkbox parameter cannot have "units" specified
        with self.assertRaises(django_exceptions.ValidationError):
            template = PartParameterTemplate(
                name='test', description='My description', units='mm', checkbox=True
            )

            template.clean()

        # Checkbox parameter cannot have "choices" specified
        with self.assertRaises(django_exceptions.ValidationError):
            template = PartParameterTemplate(
                name='test',
                description='My description',
                choices='a,b,c',
                checkbox=True,
            )

            template.clean()

        # Choices must be 'unique'
        with self.assertRaises(django_exceptions.ValidationError):
            template = PartParameterTemplate(
                name='test', description='My description', choices='a,a,b'
            )

            template.clean()

    def test_create_param(self):
        """Test that we can create a param via the API."""
        url = reverse('api-part-parameter-list')

        response = self.post(url, {'part': '2', 'template': '3', 'data': 70})

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

    def test_order_parts_by_param(self):
        """Test that we can order parts by a specified parameter."""

        def get_param_value(response, template, index):
            """Helper function to extract a parameter value from a response."""
            params = response.data[index]['parameters']

            for param in params:
                if param['template'] == template:
                    return param['data']

            # No match
            return None

        # Create a new parameter template
        template = PartParameterTemplate.objects.create(
            name='Test Template', description='My test template', units='m'
        )

        # Create parameters for each existing part
        params = []

        parts = Part.objects.all().order_by('pk')

        for idx, part in enumerate(parts):
            # Skip parts every now and then
            if idx % 10 == 7:
                continue

            suffix = 'mm' if idx % 3 == 0 else 'm'

            params.append(
                PartParameter.objects.create(
                    part=part, template=template, data=f'{idx}{suffix}'
                )
            )

        # Now, request parts, ordered by this parameter
        url = reverse('api-part-list')

        response = self.get(
            url,
            {'ordering': 'parameter_{pk}'.format(pk=template.pk), 'parameters': 'true'},
            expected_code=200,
        )

        # All parts should be returned
        self.assertEqual(len(response.data), len(parts))

        # Check that the parts are ordered correctly (in increasing order)
        expectation = {0: '0mm', 1: '3mm', 7: '4m', 9: '8m', -2: '13m', -1: None}

        for idx, expected in expectation.items():
            actual = get_param_value(response, template.pk, idx)
            self.assertEqual(actual, expected)

        # Next, check reverse ordering
        response = self.get(
            url,
            {
                'ordering': '-parameter_{pk}'.format(pk=template.pk),
                'parameters': 'true',
            },
            expected_code=200,
        )

        expectation = {0: '13m', 1: '11m', -3: '3mm', -2: '0mm', -1: None}

        for idx, expected in expectation.items():
            actual = get_param_value(response, template.pk, idx)
            self.assertEqual(actual, expected)
