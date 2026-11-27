"""Various unit tests for Part Parameters."""

import django.core.exceptions as django_exceptions
from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

import pytest

from common.models import InvenTreeSetting, Parameter, ParameterTemplate
from common.settings import set_global_setting
from InvenTree.unit_test import InvenTreeAPIPerformanceTestCase, InvenTreeAPITestCase

from .models import Part, PartCategory, PartCategoryParameterTemplate


class TestParams(TestCase):
    """Unit test class for testing the Parameter model."""

    fixtures = ['location', 'category', 'part', 'params', 'users']

    def test_str(self):
        """Test the str representation of the ParameterTemplate model."""
        t1 = ParameterTemplate.objects.get(pk=1)
        self.assertEqual(str(t1), 'Length (mm)')

        # TODO fix assertion
        # p1 = Parameter.objects.get(pk=1)
        # self.assertEqual(str(p1), 'M2x4 LPHS : Length = 4 (mm)')

        c1 = PartCategoryParameterTemplate.objects.get(pk=1)
        self.assertEqual(str(c1), 'Mechanical | Length | 2.8')

    def test_updated(self):
        """Test that the 'updated' field is correctly set."""
        p1 = Parameter.objects.get(pk=1)
        self.assertIsNone(p1.updated)
        self.assertIsNone(p1.updated_by)

        user = User.objects.get(username='sam')
        p1.save(updated_by=user)

        self.assertIsNotNone(p1.updated)
        self.assertEqual(p1.updated_by, user)

    def test_validate(self):
        """Test validation for part templates."""
        n = ParameterTemplate.objects.all().count()

        t1 = ParameterTemplate(name='abcde', units='dd')
        t1.save()

        self.assertEqual(n + 1, ParameterTemplate.objects.all().count())

        # Test that the case-insensitive name throws a ValidationError
        with self.assertRaises(django_exceptions.ValidationError):
            t3 = ParameterTemplate(name='aBcde', units='dd')
            t3.full_clean()
            t3.save()  # pragma: no cover

    def test_invalid_numbers(self):
        """Test that invalid floating point numbers are correctly handled."""
        p = Part.objects.first()
        t = ParameterTemplate.objects.create(name='Yaks')

        valid_floats = ['-12', '1.234', '17', '3e45', '-12e34']

        for value in valid_floats:
            param = Parameter(content_object=p, template=t, data=value)
            param.full_clean()
            self.assertIsNotNone(param.data_numeric)

        invalid_floats = ['88E6352', 'inf', '-inf', 'nan', '3.14.15', '3eee3']

        for value in invalid_floats:
            param = Parameter(content_object=p, template=t, data=value)
            param.full_clean()
            self.assertIsNone(param.data_numeric)

    def test_metadata(self):
        """Unit tests for the metadata field."""
        for model in [ParameterTemplate]:
            p = model.objects.first()
            assert p is not None

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

    def test_locked_part(self):
        """Test parameter editing for a locked part."""
        part = Part.objects.create(
            name='Test Part 3',
            description='A part for testing',
            category=PartCategory.objects.first(),
            IPN='TEST-PART',
        )

        parameter = Parameter.objects.create(
            content_object=part, template=ParameterTemplate.objects.first(), data='123'
        )

        # Lock the part
        part.locked = True
        part.save()

        # Attempt to edit the parameter
        with self.assertRaises(django_exceptions.ValidationError):
            parameter.data = '456'
            parameter.save()

        # Attempt to delete the parameter
        with self.assertRaises(django_exceptions.ValidationError):
            parameter.delete()

        # Unlock the part
        part.locked = False
        part.save()

        # Now we can edit the parameter
        parameter.data = '456'
        parameter.save()

        # And we can delete the parameter
        parameter.delete()

    def test_locked_part_locking_disabled(self):
        """Test that parameter restrictions are lifted when PART_ENABLE_LOCKING is disabled."""
        part = Part.objects.create(
            name='Test Part Lock Override',
            description='Part for testing global locking override',
            category=PartCategory.objects.first(),
        )

        parameter = Parameter.objects.create(
            content_object=part, template=ParameterTemplate.objects.first(), data='100'
        )

        part.locked = True
        part.save()

        # With locking enabled (default), editing and deletion are blocked
        with self.assertRaises(django_exceptions.ValidationError):
            parameter.data = '200'
            parameter.save()

        with self.assertRaises(django_exceptions.ValidationError):
            parameter.delete()

        # Disable locking globally — parameter operations should now succeed
        set_global_setting('PART_ENABLE_LOCKING', False)

        parameter.data = '200'
        parameter.save()
        self.assertEqual(parameter.data, '200')

        # Re-enable locking — editing should be blocked again
        set_global_setting('PART_ENABLE_LOCKING', True)

        with self.assertRaises(django_exceptions.ValidationError):
            parameter.data = '300'
            parameter.save()


class TestCategoryTemplates(TransactionTestCase):
    """Test class for PartCategoryParameterTemplate model."""

    fixtures = ['location', 'category', 'part', 'params']

    def test_validate(self):
        """Test that category templates are correctly applied to Part instances."""
        # Category templates
        n = PartCategoryParameterTemplate.objects.all().count()
        self.assertEqual(n, 2)

        category = PartCategory.objects.get(pk=8)

        t1 = ParameterTemplate.objects.get(pk=2)
        c1 = PartCategoryParameterTemplate(
            category=category, template=t1, default_value='xyz'
        )
        c1.save()

        n = PartCategoryParameterTemplate.objects.all().count()
        self.assertEqual(n, 3)


class ParameterTests(TestCase):
    """Unit tests for parameter validation."""

    fixtures = ['location', 'category', 'part', 'params']

    def test_choice_validation(self):
        """Test that parameter choices are correctly validated."""
        template = ParameterTemplate.objects.create(
            name='My Template',
            description='A template with choices',
            choices='red, blue, green',
        )

        pass_values = ['red', 'blue', 'green']
        fail_values = ['rod', 'bleu', 'grene']

        part = Part.objects.all().first()

        for value in pass_values:
            param = Parameter(content_object=part, template=template, data=value)
            param.full_clean()

        for value in fail_values:
            param = Parameter(content_object=part, template=template, data=value)
            with self.assertRaises(django_exceptions.ValidationError):
                param.full_clean()

    def test_unit_validation(self):
        """Test validation of 'units' field for ParameterTemplate."""
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
            tmp = ParameterTemplate(name='test', units=unit)
            tmp.full_clean()

        # Test that invalid units fail
        for unit in ['mmmmm', '-', 'x', int, "piao's"]:
            tmp = ParameterTemplate(name='test', units=unit)
            with self.assertRaises(django_exceptions.ValidationError):
                tmp.full_clean()

    def test_param_unit_validation(self):
        """Test that parameters are correctly validated against template units."""
        template = ParameterTemplate.objects.create(name='My Template', units='m')

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
            param = Parameter(content_object=prt, template=template, data=value)
            param.full_clean()

        # Test that percent unit is working
        template2 = ParameterTemplate.objects.create(name='My Template 2', units='%')
        for value in ['1', '1%', '1 percent']:
            param = Parameter(content_object=prt, template=template2, data=value)
            param.full_clean()

        bad_values = ['3 Amps', '-3 zogs', '3.14F']

        # Disable enforcing of part parameter units
        InvenTreeSetting.set_setting('PARAMETER_ENFORCE_UNITS', False, change_user=None)

        # Invalid units also pass, but will be converted to the template units
        for value in bad_values:
            param = Parameter(content_object=prt, template=template, data=value)
            param.full_clean()

        # Enable enforcing of part parameter units
        InvenTreeSetting.set_setting('PARAMETER_ENFORCE_UNITS', True, change_user=None)

        for value in bad_values:
            param = Parameter(content_object=prt, template=template, data=value)
            with self.assertRaises(django_exceptions.ValidationError):
                param.full_clean()

    def test_param_unit_conversion(self):
        """Test that parameters are correctly converted to template units."""
        template = ParameterTemplate.objects.create(name='My Template', units='m')

        tests = {
            '1': 1.0,
            '-1': -1.0,
            '23m': 23.0,
            '-89mm': -0.089,
            '100 foot': 30.48,
            '-17 yards': -15.54,
        }

        prt = Part.objects.get(pk=1)
        param = Parameter(content_object=prt, template=template, data='1')

        for value, expected in tests.items():
            param.data = value
            param.calculate_numeric_value()
            self.assertAlmostEqual(param.data_numeric, expected, places=2)


class ParameterTest(InvenTreeAPITestCase):
    """Tests for the Parameter API."""

    superuser = True

    fixtures = ['category', 'part', 'location', 'params']

    def test_list_params(self):
        """Test for listing part parameters."""
        url = reverse('api-parameter-list')

        response = self.get(url)

        self.assertEqual(len(response.data), 7)

        # Filter by part
        response = self.get(url, {'model_id': 3, 'model_type': 'part.part'})

        self.assertEqual(len(response.data), 3)

        # Filter by template
        response = self.get(url, {'template': 1})

        self.assertEqual(len(response.data), 4)

    def test_param_template_validation(self):
        """Test that part parameter template validation routines work correctly."""
        # Checkbox parameter cannot have "units" specified
        with self.assertRaises(django_exceptions.ValidationError):
            template = ParameterTemplate(
                name='test', description='My description', units='mm', checkbox=True
            )

            template.clean()

        # Checkbox parameter cannot have "choices" specified
        with self.assertRaises(django_exceptions.ValidationError):
            template = ParameterTemplate(
                name='test',
                description='My description',
                choices='a,b,c',
                checkbox=True,
            )

            template.clean()

        # Choices must be 'unique'
        with self.assertRaises(django_exceptions.ValidationError):
            template = ParameterTemplate(
                name='test', description='My description', choices='a,a,b'
            )

            template.clean()

    def test_create_param(self):
        """Test that we can create a param via the API."""
        url = reverse('api-parameter-list')

        response = self.post(
            url,
            {'model_id': '2', 'model_type': 'part.part', 'template': '3', 'data': 70},
        )

        self.assertEqual(response.status_code, 201)

        response = self.get(url)

        self.assertEqual(len(response.data), 8)

    def test_bulk_create_params(self):
        """Test that we can bulk create parameters via the API."""
        url = reverse('api-parameter-list')
        part4 = Part.objects.get(pk=4)

        data = [
            {'model_id': 4, 'model_type': 'part.part', 'template': 1, 'data': 70},
            {'model_id': 4, 'model_type': 'part.part', 'template': 2, 'data': 80},
            {'model_id': 4, 'model_type': 'part.part', 'template': 1, 'data': 80},
        ]

        # test that having non unique part/template combinations fails
        res = self.post(url, data, expected_code=400)

        self.assertEqual(len(res.data), 3)
        self.assertEqual(len(res.data[1]), 0)
        for err in [res.data[0], res.data[2]]:
            self.assertEqual(len(err), 3)
            self.assertEqual(str(err['model_id'][0]), 'This field must be unique.')
            self.assertEqual(str(err['model_type'][0]), 'This field must be unique.')
            self.assertEqual(str(err['template'][0]), 'This field must be unique.')

        self.assertEqual(
            Parameter.objects.filter(
                model_type=part4.get_content_type(), model_id=part4.pk
            ).count(),
            0,
        )

        # Now, create a valid set of parameters
        data = [
            {'model_id': 4, 'model_type': 'part.part', 'template': 1, 'data': 70},
            {'model_id': 4, 'model_type': 'part.part', 'template': 2, 'data': 80},
        ]
        res = self.post(url, data, expected_code=201)
        self.assertEqual(len(res.data), 2)

        self.assertEqual(
            Parameter.objects.filter(
                model_type=part4.get_content_type(), model_id=part4.pk
            ).count(),
            2,
        )

    def test_param_detail(self):
        """Tests for the Parameter detail endpoint."""
        url = reverse('api-parameter-detail', kwargs={'pk': 5})

        response = self.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.data

        self.assertEqual(data['pk'], 5)
        self.assertEqual(data['model_id'], 3)
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
        template = ParameterTemplate.objects.create(
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
                Parameter.objects.create(
                    content_object=part, template=template, data=f'{idx}{suffix}'
                )
            )

        # Now, request parts, ordered by this parameter
        url = reverse('api-part-list')

        response = self.get(
            url,
            {'ordering': f'parameter_{template.pk}', 'parameters': 'true'},
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
            {'ordering': f'-parameter_{template.pk}', 'parameters': 'true'},
            expected_code=200,
        )

        expectation = {0: '13m', 1: '11m', -3: '3mm', -2: '0mm', -1: None}

        for idx, expected in expectation.items():
            actual = get_param_value(response, template.pk, idx)
            self.assertEqual(actual, expected)


class ParametricDataMixin:
    """Mixin which creates a set of parts with parametric data for testing.

    Provides a 'create_parts' helper, so that tests can increase the size
    of the dataset (e.g. to check that query counts do not scale with the
    number of results).
    """

    @classmethod
    def setUpTestData(cls):
        """Setup test data for the parametric tests."""
        super().setUpTestData()

        cls.url = reverse('api-part-list')

        # Create a number of part parameter templates
        cls.template_length = ParameterTemplate.objects.create(
            name='Length', description='Length of the part', units='mm'
        )

        cls.template_width = ParameterTemplate.objects.create(
            name='Width', description='Width of the part', units='mm'
        )

        cls.template_ionized = ParameterTemplate.objects.create(
            name='Ionized', description='Is the part ionized?', checkbox=True
        )

        cls.template_color = ParameterTemplate.objects.create(
            name='Color', description='Color of the part', choices='red,green,blue'
        )

        cls.category = PartCategory.objects.create(
            name='Test Category', description='A category for testing part parameters'
        )

        cls.create_parts(50)

    @classmethod
    def create_parts(cls, count: int, offset: int = 0) -> list[Part]:
        """Bulk-create a number of parts, with associated parameter data.

        Arguments:
            count: The number of parts to create
            offset: Index offset (used to generate unique names and values)

        Returns:
            The list of created parts
        """
        from InvenTree.helpers_db import bulk_create_and_fetch

        parts = bulk_create_and_fetch(
            Part,
            [
                Part(
                    name=f'Part {i}',
                    description=f'Description for part {i}',
                    category=cls.category,
                    IPN=f'PART-{i:03d}',
                    level=0,
                    tree_id=0,
                    lft=0,
                    rght=0,
                )
                for i in range(offset + 1, offset + count + 1)
            ],
        )

        # Create parameters for each part
        parameters = []

        for jj, part in enumerate(parts):
            ii = jj + offset

            parameters.append(
                Parameter(
                    content_object=part,
                    template=cls.template_length,
                    data=(ii * 10) + 5,  # Length in mm
                    data_numeric=(ii * 10) + 5,  # Numeric value for length
                )
            )

            parameters.append(
                Parameter(
                    content_object=part,
                    template=cls.template_width,
                    data=(50 - ii) * 5 + 2,  # Width in mm
                    data_numeric=(50 - ii) * 5 + 2,  # Width in mm
                )
            )

            # Only some parts have 'ionized' and 'color' parameters (repeats every 50 parts)
            if ii % 50 < 25:
                parameters.append(
                    Parameter(
                        content_object=part,
                        template=cls.template_ionized,
                        data='true'
                        if ii % 5 == 0
                        else 'false',  # Ionized every fifth part
                        data_numeric=1 if ii % 5 == 0 else 0,
                    )
                )

            if ii % 50 < 15:
                parameters.append(
                    Parameter(
                        content_object=part,
                        template=cls.template_color,
                        data=['red', 'green', 'blue'][ii % 3],  # Cycle through colors
                        data_numeric=None,  # No numeric value for color
                    )
                )

        # Bulk create all parameters
        Parameter.objects.bulk_create(parameters)

        return parts


class ParameterFilterTest(ParametricDataMixin, InvenTreeAPITestCase):
    """Unit tests for filtering parts by parameter values."""

    superuser = True

    def test_filter_by_length(self):
        """Test basic filtering by length parameter."""
        length_filters = [
            ('_lt', '25', 2),
            ('_lt', '25 mm', 2),
            ('_gt', '1 inch', 47),
            ('', '105', 1),
            ('_lt', '2 mile', 50),
        ]

        for operator, value, expected_count in length_filters:
            filter_name = f'parameter_{self.template_length.pk}' + operator
            response = self.get(self.url, {filter_name: value}, expected_code=200).data

            self.assertEqual(len(response), expected_count)

    def test_filter_by_width(self):
        """Test basic filtering by width parameter."""
        width_filters = [
            ('_lt', '102', 19),
            ('_lte', '102 mm', 20),
            ('_gte', '0.1 yards', 33),
            ('', '52mm', 1),
        ]

        for operator, value, expected_count in width_filters:
            filter_name = f'parameter_{self.template_width.pk}' + operator
            response = self.get(self.url, {filter_name: value}, expected_code=200).data

            self.assertEqual(len(response), expected_count)

    def test_filter_by_ionized(self):
        """Test filtering by ionized parameter."""
        ionized_filters = [
            ('', 'true', 5),  # Ionized parts
            ('', 'false', 20),  # Non-ionized parts
        ]

        for operator, value, expected_count in ionized_filters:
            filter_name = f'parameter_{self.template_ionized.pk}' + operator
            response = self.get(self.url, {filter_name: value}, expected_code=200).data

            self.assertEqual(len(response), expected_count)

    def test_filter_by_color(self):
        """Test filtering by color parameter."""
        for color in ['red', 'green', 'blue']:
            response = self.get(
                self.url,
                {f'parameter_{self.template_color.pk}': color},
                expected_code=200,
            ).data

            self.assertEqual(len(response), 5)

    def test_filter_si_prefix(self):
        """Test filtering by values which differ only in SI prefix.

        Unit conversion introduces floating point error (e.g. '100nF' != '0.1uF'),
        so numeric comparisons must be tolerant of this.
        """
        template = ParameterTemplate.objects.create(
            name='Capacitance', description='Capacitance of the part', units='F'
        )

        values = ['10nF', '100nF', '0.1uF', '1uF', '1000nF']
        parts = list(Part.objects.all()[: len(values)])

        for part, value in zip(parts, values, strict=True):
            Parameter.objects.create(content_object=part, template=template, data=value)

        filters = [
            ('', '100n', 2),
            ('', '100nF', 2),
            ('', '0.1u', 2),
            ('', '.1uF', 2),
            ('', '100000pF', 2),
            ('', '1uF', 2),
            ('', '1000n', 2),
            ('', '0.01u', 1),
            ('', '101nF', 0),
            ('_ne', '0.1uF', 48),
            ('_gt', '0.1uF', 2),
            ('_gte', '100nF', 4),
            ('_lt', '100nF', 1),
            ('_lte', '0.1uF', 3),
            ('_gt', '1000nF', 0),
            ('_gte', '1uF', 2),
            ('_lt', '1uF', 3),
            ('_lte', '1000nF', 5),
        ]

        for operator, value, expected_count in filters:
            filter_name = f'parameter_{template.pk}' + operator
            response = self.get(self.url, {filter_name: value}, expected_code=200).data

            self.assertEqual(len(response), expected_count, f'{filter_name}={value}')

    def test_filter_ne_same_template(self):
        """The '_ne' filter must only consider parameters for the specified template.

        A value of 7mm exists for the 'width' template (one part),
        but no part has a 'length' of 7mm - so no parts should be excluded.
        """
        response = self.get(
            self.url, {f'parameter_{self.template_width.pk}': '7'}, expected_code=200
        )
        self.assertEqual(len(response.data), 1)

        response = self.get(
            self.url,
            {f'parameter_{self.template_length.pk}_ne': '7'},
            expected_code=200,
        )
        self.assertEqual(len(response.data), 50)

        # Excludes only the single part which has a 'length' of 15mm
        response = self.get(
            self.url,
            {f'parameter_{self.template_length.pk}_ne': '15'},
            expected_code=200,
        )
        self.assertEqual(len(response.data), 49)

    def test_filter_multiple(self):
        """Test filtering by multiple parameters."""
        data = {f'parameter_{self.template_length.pk}_lt': '225'}
        response = self.get(self.url, data)
        self.assertEqual(len(response.data), 22)

        data[f'parameter_{self.template_width.pk}_gt'] = '150'
        response = self.get(self.url, data)
        self.assertEqual(len(response.data), 21)

        data[f'parameter_{self.template_ionized.pk}'] = 'true'
        response = self.get(self.url, data)
        self.assertEqual(len(response.data), 5)

        for color in ['red', 'green', 'blue']:
            data[f'parameter_{self.template_color.pk}'] = color
            response = self.get(self.url, data)
            self.assertEqual(len(response.data), 1)


class ParametricQueryTest(ParametricDataMixin, InvenTreeAPITestCase):
    """Regression tests for the database cost of parametric part queries.

    These tests guard against:
    - "N + 1" query regressions (query count must not scale with results)
    - Re-introduction of DISTINCT queries for parameter filtering, which force
      the database to evaluate every annotation for every matching row
    """

    superuser = True

    # Upper bound on the number of queries for any single parametric request
    MAX_PARAMETRIC_QUERIES = 25

    def parametric_queries(self) -> dict[str, dict]:
        """Return a set of representative parametric queries."""
        length = self.template_length.pk
        width = self.template_width.pk
        ionized = self.template_ionized.pk
        color = self.template_color.pk

        complex_query = {
            'category': self.category.pk,
            'cascade': True,
            'category_detail': True,
            'parameters': True,
            'ordering': f'-parameter_{length}',
            f'parameter_{length}_gt': '20',
            f'parameter_{width}_lte': '1000mm',
            f'parameter_{color}_ne': 'red',
        }

        return {
            'parameters': {'parameters': True},
            'order': {'ordering': f'parameter_{length}', 'parameters': True},
            'order_desc': {'ordering': f'-parameter_{width}', 'parameters': True},
            'filter_gt': {f'parameter_{length}_gt': '20', 'parameters': True},
            'filter_units': {f'parameter_{width}_lt': '1 m', 'parameters': True},
            'filter_ne': {f'parameter_{length}_ne': '15', 'parameters': True},
            'filter_text': {f'parameter_{color}_icontains': 'e', 'parameters': True},
            'filter_bool': {f'parameter_{ionized}': 'false', 'parameters': True},
            'complex': complex_query,
            'complex_paginated': {**complex_query, 'limit': 10, 'offset': 5},
        }

    def capture(self, params: dict):
        """Perform a part list query, and capture the executed queries."""
        with CaptureQueriesContext(connection) as ctx:
            response = self.get(self.url, params, expected_code=200)

        return response, ctx

    @staticmethod
    def result_count(response) -> int:
        """Return the total number of results for a (possibly paginated) response."""
        data = response.data
        return data['count'] if isinstance(data, dict) else len(data)

    def test_query_count_constant(self):
        """The number of queries must not scale with the number of results ("N + 1")."""
        queries = self.parametric_queries()

        # Warm up any caches (content types, settings, etc)
        for params in queries.values():
            self.get(self.url, params, expected_code=200)

        baseline = {}

        for name, params in queries.items():
            response, ctx = self.capture(params)
            baseline[name] = (len(ctx), self.result_count(response))

            self.assertLess(
                len(ctx),
                self.MAX_PARAMETRIC_QUERIES,
                f"Too many queries for '{name}': {len(ctx)}",
            )

        # Triple the size of the dataset
        self.create_parts(100, offset=50)

        for name, params in queries.items():
            response, ctx = self.capture(params)
            n_queries, n_results = baseline[name]

            # Ensure that the larger dataset is actually reflected in the results
            self.assertGreater(
                self.result_count(response),
                n_results,
                f"Expected more results for '{name}'",
            )

            self.assertEqual(
                len(ctx),
                n_queries,
                f"Query count for '{name}' changed with dataset size: "
                f'{n_queries} -> {len(ctx)}',
            )

    def test_parameters_prefetched(self):
        """Serializing parameters must not trigger per-part or per-parameter queries."""
        without = self.capture({'limit': 100})[1]
        response, with_params = self.capture({'limit': 100, 'parameters': True})

        # Every part has at least two parameters, each with nested template data
        n_params = sum(len(part['parameters']) for part in response.data['results'])
        self.assertGreaterEqual(n_params, 100)

        for part in response.data['results']:
            for param in part['parameters']:
                self.assertIsNotNone(param['template_detail'])

        # Parameter data should be loaded via a small, fixed number of prefetch queries
        self.assertLessEqual(len(with_params) - len(without), 5)

    def test_filter_no_distinct(self):
        """Parameter filtering must not produce SELECT DISTINCT queries.

        Joining against the parameter table and de-duplicating with DISTINCT
        forces the database to evaluate all queryset annotations for every
        matching row (both for the results and the pagination count query).
        """
        for name, params in self.parametric_queries().items():
            _response, ctx = self.capture({**params, 'limit': 10})

            for query in ctx.captured_queries:
                sql = query['sql'].upper()

                self.assertFalse(
                    'SELECT DISTINCT' in sql and 'PART_PART' in sql,
                    f"Unexpected DISTINCT query for '{name}': {query['sql'][:200]}",
                )

    def test_filter_no_duplicates(self):
        """Filtering against multiple parameters must not return duplicate rows."""
        length = self.template_length.pk
        width = self.template_width.pk

        response, _ctx = self.capture({
            f'parameter_{length}_gt': '20',
            f'parameter_{width}_gt': '20',
            'limit': 100,
        })

        pks = [part['pk'] for part in response.data['results']]

        # No duplicate rows are returned
        self.assertEqual(len(pks), len(set(pks)))
        self.assertEqual(response.data['count'], len(pks))


class ParametricApiPerformanceTest(
    ParametricDataMixin, InvenTreeAPIPerformanceTestCase
):
    """Performance benchmarks for parametric part queries."""

    superuser = True

    @classmethod
    def setUpTestData(cls):
        """Create a larger dataset for benchmarking."""
        super().setUpTestData()
        cls.create_parts(450, offset=50)

    @pytest.mark.django_db
    @pytest.mark.benchmark
    def test_api_part_list_parameters(self):
        """Benchmark the part list with parameter data and ordering."""
        response = self.get(
            self.url,
            {
                'parameters': True,
                'ordering': f'-parameter_{self.template_length.pk}',
                'limit': 25,
            },
            expected_code=200,
        )
        self.assertEqual(response.data['count'], 500)

    @pytest.mark.django_db
    @pytest.mark.benchmark
    def test_api_part_list_parametric_filter(self):
        """Benchmark the part list filtered against multiple parameters."""
        response = self.get(
            self.url,
            {
                'category': self.category.pk,
                'cascade': True,
                'category_detail': True,
                'parameters': True,
                'ordering': f'-parameter_{self.template_length.pk}',
                f'parameter_{self.template_length.pk}_gt': '100',
                f'parameter_{self.template_width.pk}_lt': '1 m',
                'limit': 25,
            },
            expected_code=200,
        )
        self.assertGreater(response.data['count'], 0)
