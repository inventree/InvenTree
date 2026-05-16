"""Various unit tests for Part Parameters."""

import django.core.exceptions as django_exceptions
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from common.models import InvenTreeSetting, Parameter, ParameterTemplate
from InvenTree.unit_test import InvenTreeAPITestCase

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
        for unit in ['mmmmm', '-', 'x', int]:
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


class ParameterFilterTest(InvenTreeAPITestCase):
    """Unit tests for filtering parts by parameter values."""

    superuser = True

    @classmethod
    def setUpTestData(cls):
        """Setup test data for the filtering tests."""
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

        # Create a number of parts
        parts = [
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
            for i in range(1, 51)
        ]

        Part.objects.bulk_create(parts)

        # Create parameters for each part
        parameters = []

        for ii, part in enumerate(Part.objects.all()):
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

            if ii < 25:
                parameters.append(
                    Parameter(
                        content_object=part,
                        template=cls.template_ionized,
                        data='true'
                        if ii % 5 == 0
                        else 'false',  # Ionized every second part
                        data_numeric=1
                        if ii % 5 == 0
                        else 0,  # Ionized every second part
                    )
                )

            if ii < 15:
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
