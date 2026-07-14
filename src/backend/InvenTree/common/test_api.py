"""API unit tests for InvenTree common functionality."""

import io

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from PIL import Image
from taggit.models import Tag

import common.models
from common.models import SelectionList, SelectionListEntry
from InvenTree.unit_test import InvenTreeAPITestCase


class DataOutputAPITests(InvenTreeAPITestCase):
    """API tests for the DataOutput endpoint."""

    roles = 'all'

    def setUp(self):
        """Set up some test data for DataOutput API testing."""
        from report.models import DataOutput

        super().setUp()

        for ii in range(5):
            DataOutput.objects.create(
                output_type='test_output',
                user=self.user if ii % 2 == 0 else None,
                complete=ii % 2 == 1,
            )

    def test_data_output_list(self):
        """Test the DataOutput API list endpoint."""
        url = reverse('api-data-output-list')

        #  Non-staff user should only see outputs which are either enabled for all users, or created by themselves
        self.user.is_staff = False
        self.user.save()
        response = self.get(url)
        self.assertEqual(len(response.data), 3)

        for output in response.data:
            self.assertEqual(output['user'], self.user.pk)

        # Set staff access = True, so we should see all outputs
        self.user.is_staff = True
        self.user.save()
        response = self.get(url)
        self.assertEqual(len(response.data), 5)


class ParameterAPITests(InvenTreeAPITestCase):
    """Tests for the Parameter API."""

    roles = 'all'

    def test_template_options(self):
        """Test OPTIONS information for the ParameterTemplate API endpoint."""
        url = reverse('api-parameter-template-list')

        options = self.options(url)
        actions = options.data['actions']['GET']

        for field in [
            'pk',
            'name',
            'units',
            'description',
            'model_type',
            'selectionlist',
            'enabled',
            'unique',
        ]:
            self.assertIn(
                field,
                actions.keys(),
                f'Field "{field}" missing from ParameterTemplate API!',
            )

        model_types = [act['value'] for act in actions['model_type']['choices']]

        for mdl in [
            'part.part',
            'build.build',
            'company.company',
            'order.purchaseorder',
        ]:
            self.assertIn(
                mdl,
                model_types,
                f'Model type "{mdl}" missing from ParameterTemplate API!',
            )

    def test_parameter_options(self):
        """Test OPTIONS information for the Parameter API endpoint."""
        url = reverse('api-parameter-list')

        options = self.options(url)
        actions = options.data['actions']['GET']

        for field in [
            'pk',
            'template',
            'model_type',
            'model_id',
            'data',
            'data_numeric',
        ]:
            self.assertIn(
                field, actions.keys(), f'Field "{field}" missing from Parameter API!'
            )

        self.assertFalse(actions['data']['read_only'])
        self.assertFalse(actions['model_type']['read_only'])

    def test_template_api(self):
        """Test ParameterTemplate API functionality."""
        url = reverse('api-parameter-template-list')

        N = common.models.ParameterTemplate.objects.count()

        # Create a new ParameterTemplate - initially with invalid model_type field
        data = {
            'name': 'Test Parameter',
            'units': 'mm',
            'description': 'A test parameter template',
            'model_type': 'order.salesorderx',
            'enabled': True,
        }

        response = self.post(url, data, expected_code=400)
        self.assertIn('Content type not found', str(response.data['model_type']))

        data['model_type'] = 'order.salesorder'

        response = self.post(url, data, expected_code=201)
        pk = response.data['pk']

        # Verify that the ParameterTemplate was created
        self.assertEqual(common.models.ParameterTemplate.objects.count(), N + 1)

        template = common.models.ParameterTemplate.objects.get(pk=pk)
        self.assertEqual(template.name, 'Test Parameter')
        self.assertEqual(template.description, 'A test parameter template')
        self.assertEqual(template.units, 'mm')

        # Let's update the Template via the API
        data = {'description': 'An UPDATED test parameter template'}

        response = self.patch(
            reverse('api-parameter-template-detail', kwargs={'pk': pk}),
            data,
            expected_code=200,
        )

        template.refresh_from_db()
        self.assertEqual(template.description, 'An UPDATED test parameter template')

        # Finally, let's delete the Template
        response = self.delete(
            reverse('api-parameter-template-detail', kwargs={'pk': pk}),
            expected_code=204,
        )

        self.assertEqual(common.models.ParameterTemplate.objects.count(), N)
        self.assertFalse(common.models.ParameterTemplate.objects.filter(pk=pk).exists())

        # Let's create a template which does not specify a model_type
        data = {
            'name': 'Universal Parameter',
            'units': '',
            'description': 'A parameter template for all models',
            'enabled': False,
        }

        response = self.post(url, data, expected_code=201)

        self.assertIsNone(response.data['model_type'])
        self.assertFalse(response.data['enabled'])

    def test_template_filters(self):
        """Tests for API filters against ParameterTemplate endpoint."""
        from company.models import Company

        # Create some ParameterTemplate objects
        t1 = common.models.ParameterTemplate.objects.create(
            name='Template A',
            description='Template with choices',
            choices='apple,banana,cherry',
            enabled=True,
        )

        t2 = common.models.ParameterTemplate.objects.create(
            name='Template B',
            description='Template without choices',
            enabled=True,
            units='mm',
            model_type=Company.get_content_type(),
        )

        t3 = common.models.ParameterTemplate.objects.create(
            name='Template C', description='Another template', enabled=False
        )

        url = reverse('api-parameter-template-list')

        # Filter by 'enabled' status
        response = self.get(url, data={'enabled': True})
        self.assertEqual(len(response.data), 2)

        response = self.get(url, data={'enabled': False})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], t3.pk)

        # Filter by 'has_choices'
        response = self.get(url, data={'has_choices': True})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], t1.pk)

        response = self.get(url, data={'has_choices': False})
        self.assertEqual(len(response.data), 2)

        # Filter by 'model_type'
        response = self.get(url, data={'model_type': 'company.company'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], t2.pk)

        # Filter by 'has_units'
        response = self.get(url, data={'has_units': True})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], t2.pk)

        response = self.get(url, data={'has_units': False})
        self.assertEqual(len(response.data), 2)

        # Filter by 'for_model'
        # Note that a 'blank' model_type is considered to match all models
        response = self.get(url, data={'for_model': 'part.part'})
        self.assertEqual(len(response.data), 2)

        response = self.get(url, data={'for_model': 'company'})
        self.assertEqual(len(response.data), 3)

        # Create a Parameter against a specific Company instance
        company = Company.objects.create(
            name='Test Company', description='A company for testing'
        )

        common.models.Parameter.objects.create(
            template=t1,
            model_type=company.get_content_type(),
            model_id=company.pk,
            data='apple',
        )

        model_types = {'company': 3, 'part.part': 2, 'order.purchaseorder': 2}

        for model_name, count in model_types.items():
            response = self.get(url, data={'for_model': model_name})
            self.assertEqual(
                len(response.data),
                count,
                f'Incorrect number of templates for model "{model_name}"',
            )

        # Filter with an invalid 'for_model'
        response = self.get(
            url, data={'for_model': 'invalid.modelname'}, expected_code=400
        )

        self.assertIn('Invalid content type: invalid.modelname', str(response.data))

        # Filter the "exists for model" filter
        model_types = {'company': 1, 'part.part': 0, 'order.purchaseorder': 0}

        for model_name, count in model_types.items():
            response = self.get(url, data={'exists_for_model': model_name})
            self.assertEqual(
                len(response.data),
                count,
                f'Incorrect number of templates for model "{model_name}"',
            )

    def test_template_extended_filters(self):
        """Unit testing for more complex filters on the ParameterTemplate endpoint.

        Ref: https://github.com/inventree/InvenTree/pull/11383

        In these tests we will filter by complex model relations.
        """
        from part.models import Part, PartCategory

        # Create some part categories
        cat_mech = PartCategory.objects.create(
            name='Mechanical', description='Mechanical components'
        )
        cat_elec = PartCategory.objects.create(
            name='Electronics', description='Electronic components'
        )
        cat_pass = PartCategory.objects.create(
            name='Passive', description='Passive electronic components', parent=cat_elec
        )
        cat_res = PartCategory.objects.create(
            name='Resistors', description='Resistor components', parent=cat_pass
        )
        cat_cap = PartCategory.objects.create(
            name='Capacitors', description='Capacitor components', parent=cat_pass
        )

        # Create some parts
        capacitors = [
            Part.objects.create(
                name=f'Capacitor {ii}', description='A capacitor', category=cat_cap
            )
            for ii in range(5)
        ]

        resistors = [
            Part.objects.create(
                name=f'Resistor {ii}', description='A resistor', category=cat_res
            )
            for ii in range(5)
        ]

        # Create some ParameterTemplates which relate to the category of the part
        resistance = common.models.ParameterTemplate.objects.create(
            name='Resistance', description='The resistance of a part', units='Ohms'
        )

        capacitance = common.models.ParameterTemplate.objects.create(
            name='Capacitance', description='The capacitance of a part', units='Farads'
        )

        tolerance = common.models.ParameterTemplate.objects.create(
            name='Tolerance', description='The tolerance of a part', units='%'
        )

        for idx, resistor in enumerate(resistors):
            common.models.Parameter.objects.create(
                template=resistance,
                model_type=resistor.get_content_type(),
                model_id=resistor.pk,
                data=f'{10 * (idx + 1)}k',
            )

            common.models.Parameter.objects.create(
                template=tolerance,
                model_type=resistor.get_content_type(),
                model_id=resistor.pk,
                data=f'{idx + 1}%',
            )

        for idx, capacitor in enumerate(capacitors):
            common.models.Parameter.objects.create(
                template=capacitance,
                model_type=capacitor.get_content_type(),
                model_id=capacitor.pk,
                data=f'{10 * (idx + 1)}uF',
            )

            common.models.Parameter.objects.create(
                template=tolerance,
                model_type=capacitor.get_content_type(),
                model_id=capacitor.pk,
                data=f'{5 * (idx + 1)}%',
            )

        # Ensure that we have the expected number of templates and parameters created for testing
        self.assertEqual(common.models.ParameterTemplate.objects.count(), 3)
        self.assertEqual(common.models.Parameter.objects.count(), 20)

        # Now, we have some data - let's apply some filtering
        url = reverse('api-parameter-template-list')

        # Return *all* results, without filters
        response = self.get(url)
        self.assertEqual(len(response.data), 3)

        # Filter by 'exists_for_model'
        for model_name, count in {
            'part.part': 3,
            'part': 3,
            'company': 0,
            'build': 0,
        }.items():
            response = self.get(url, data={'exists_for_model': model_name})
            n = len(response.data)
            self.assertEqual(
                n,
                count,
                f'Incorrect number of templates ({n}) for model "{model_name}"',
            )

        # Filter by 'exists_for_model' and 'exists_for_model_id'
        res = resistors[0]
        response = self.get(
            url, data={'exists_for_model': 'part.part', 'exists_for_model_id': res.pk}
        )

        self.assertEqual(len(response.data), 2)
        pk_list = [t['pk'] for t in response.data]
        self.assertIn(resistance.pk, pk_list)
        self.assertIn(tolerance.pk, pk_list)

        cap = capacitors[0]
        response = self.get(
            url, data={'exists_for_model': 'part.part', 'exists_for_model_id': cap.pk}
        )
        self.assertEqual(len(response.data), 2)
        pk_list = [t['pk'] for t in response.data]
        self.assertIn(capacitance.pk, pk_list)
        self.assertIn(tolerance.pk, pk_list)

        # Filter by 'exists_for_related_model' (test the "capacitor" relationship)

        # Check the 'capacitor' category
        response = self.get(
            url,
            data={
                'exists_for_model': 'part.part',
                'exists_for_related_model': 'category',
                'exists_for_related_model_id': cat_cap.pk,
            },
        )

        self.assertEqual(len(response.data), 2)
        pk_list = [t['pk'] for t in response.data]
        self.assertIn(capacitance.pk, pk_list)
        self.assertIn(tolerance.pk, pk_list)

        # Check the 'electronics' category - this should return all parameters
        response = self.get(
            url,
            data={
                'exists_for_model': 'part.part',
                'exists_for_related_model': 'category',
                'exists_for_related_model_id': cat_elec.pk,
            },
        )
        self.assertEqual(len(response.data), 3)
        pk_list = [t['pk'] for t in response.data]
        self.assertIn(resistance.pk, pk_list)
        self.assertIn(capacitance.pk, pk_list)
        self.assertIn(tolerance.pk, pk_list)

        # Check the 'mechanical' category - this should return no parameters
        response = self.get(
            url,
            data={
                'exists_for_model': 'part.part',
                'exists_for_related_model': 'category',
                'exists_for_related_model_id': cat_mech.pk,
            },
        )

        self.assertEqual(len(response.data), 0)

    def test_invalid_filters(self):
        """Test error messages for invalid filter combinations."""
        url = reverse('api-parameter-template-list')

        # Invalid 'exists_for_model' value
        response = self.get(
            url, {'exists_for_model': 'asdf---invalid---model'}, expected_code=400
        )

        self.assertIn(
            'Invalid model type provided', str(response.data['exists_for_model'])
        )

        # Invalid 'exists_for_model_id' value
        for model_id in ['not_an_integer', -1, 9999]:
            response = self.get(
                url,
                {'exists_for_model': 'part.part', 'exists_for_model_id': model_id},
                expected_code=400,
            )

        # Invalid 'exists_for_related_model' value
        response = self.get(
            url,
            {
                'exists_for_model': 'part',
                'exists_for_related_model': 'invalid_field',
                'exists_for_related_model_id': 1,
            },
            expected_code=400,
        )

        self.assertIn(
            'no such field on the base model',
            str(response.data['exists_for_related_model']),
        )

    def test_parameter_api(self):
        """Test Parameter API functionality."""
        # Create a simple part to test with
        from part.models import Part

        part = Part.objects.create(name='Test Part', description='A part for testing')

        N = common.models.Parameter.objects.count()

        # Create a ParameterTemplate for the Part model
        template = common.models.ParameterTemplate.objects.create(
            name='Length',
            units='mm',
            model_type=part.get_content_type(),
            description='Length of part',
            enabled=True,
        )

        # Create a Parameter via the API
        url = reverse('api-parameter-list')

        data = {
            'template': template.pk,
            'model_type': 'part.part',
            'model_id': part.pk,
            'data': '25.4',
        }

        # Initially, user does not have correct permissions
        response = self.post(url, data=data, expected_code=403)

        self.assertIn(
            'User does not have permission to create or edit parameters for this model',
            str(response.data['detail']),
        )

        # Grant user the correct permissions
        self.assignRole('part.add')

        response = self.post(url, data=data, expected_code=201)

        parameter = common.models.Parameter.objects.get(pk=response.data['pk'])

        # Check that the Parameter was created
        self.assertEqual(common.models.Parameter.objects.count(), N + 1)

        # Try to create a duplicate Parameter (should fail)
        response = self.post(url, data=data, expected_code=400)

        self.assertIn(
            'The fields model_type, model_id, template must make a unique set.',
            str(response.data['non_field_errors']),
        )

        # Let's edit the Parameter via the API
        url = reverse('api-parameter-detail', kwargs={'pk': parameter.pk})

        response = self.patch(url, data={'data': '-2 inches'}, expected_code=200)

        # Ensure parameter conversion has correctly updated data_numeric field
        data = response.data
        self.assertEqual(data['data'], '-2 inches')
        self.assertAlmostEqual(data['data_numeric'], -50.8, places=2)

        # Finally, delete the Parameter via the API
        response = self.delete(url, expected_code=204)

        self.assertEqual(common.models.Parameter.objects.count(), N)
        self.assertFalse(
            common.models.Parameter.objects.filter(pk=parameter.pk).exists()
        )

    def test_parameter_uniqueness(self):
        """Test the uniqueness options which can be applied to a ParameterTemplate."""
        from company.models import Company
        from part.models import Part

        part_a = Part.objects.create(name='Part A', description='A part for testing')
        part_b = Part.objects.create(name='Part B', description='A part for testing')
        part_c = Part.objects.create(name='Part C', description='A part for testing')
        company = Company.objects.create(
            name='Test Company', description='A company for testing'
        )

        template = common.models.ParameterTemplate.objects.create(
            name='Serial Number', description='A serial number parameter'
        )

        self.assertEqual(
            template.unique, common.models.ParameterTemplate.UniqueOptions.NONE
        )

        param_a = common.models.Parameter(
            template=template,
            model_type=part_a.get_content_type(),
            model_id=part_a.pk,
            data='ABC123',
        )
        param_a.full_clean()
        param_a.save()

        # No uniqueness requirement - a duplicate value against a different part is fine
        param_b = common.models.Parameter(
            template=template,
            model_type=part_b.get_content_type(),
            model_id=part_b.pk,
            data='ABC123',
        )
        param_b.full_clean()
        param_b.save()

        # Re-saving the existing instance (unchanged) should not raise any errors
        param_a.full_clean()
        param_a.save()

        # Now, require uniqueness *per model type*
        template.unique = common.models.ParameterTemplate.UniqueOptions.MODEL_TYPE
        template.save()

        # A new Part with the same value should be rejected
        with self.assertRaises(ValidationError):
            common.models.Parameter(
                template=template,
                model_type=part_c.get_content_type(),
                model_id=part_c.pk,
                data='ABC123',
            ).full_clean()

        # A case-insensitive match should also be rejected
        with self.assertRaises(ValidationError):
            common.models.Parameter(
                template=template,
                model_type=part_c.get_content_type(),
                model_id=part_c.pk,
                data='abc123',
            ).full_clean()

        # A different model type entirely is not affected by the 'model type' restriction
        param_company = common.models.Parameter(
            template=template,
            model_type=company.get_content_type(),
            model_id=company.pk,
            data='ABC123',
        )
        param_company.full_clean()
        param_company.save()

        # Finally, require the value to be *globally* unique
        template.unique = common.models.ParameterTemplate.UniqueOptions.GLOBAL
        template.save()

        with self.assertRaises(ValidationError):
            common.models.Parameter(
                template=template,
                model_type=part_c.get_content_type(),
                model_id=part_c.pk,
                data='ABC123',
            ).full_clean()

    def test_parameter_uniqueness_units(self):
        """Test that uniqueness checks are unit-aware for templates which define units.

        Values expressed in different (but compatible) units which represent the
        same physical quantity must be detected as duplicates.
        """
        from part.models import Part

        part_a = Part.objects.create(name='Part A', description='A part for testing')
        part_b = Part.objects.create(name='Part B', description='A part for testing')

        template = common.models.ParameterTemplate.objects.create(
            name='Resistance',
            units='ohm',
            description='A globally unique resistance parameter',
            unique=common.models.ParameterTemplate.UniqueOptions.GLOBAL,
        )

        param_a = common.models.Parameter(
            template=template,
            model_type=part_a.get_content_type(),
            model_id=part_a.pk,
            data='1000',
        )
        param_a.full_clean()
        param_a.save()

        # A value expressed as '1k' ohms is numerically identical to '1000' ohms
        with self.assertRaises(ValidationError):
            common.models.Parameter(
                template=template,
                model_type=part_b.get_content_type(),
                model_id=part_b.pk,
                data='1k',
            ).full_clean()

        # A distinct value (in different units) is not a duplicate
        param_b = common.models.Parameter(
            template=template,
            model_type=part_b.get_content_type(),
            model_id=part_b.pk,
            data='2k',
        )
        param_b.full_clean()
        param_b.save()

    def test_copy_unique_parameters(self):
        """Test that 'unique' parameters are skipped when copying parameters between model instances."""
        from part.models import Part

        part_a = Part.objects.create(name='Part A', description='A part for testing')
        part_b = Part.objects.create(name='Part B', description='A part for testing')

        normal_template = common.models.ParameterTemplate.objects.create(
            name='Color', description='A normal (non-unique) parameter'
        )

        unique_template = common.models.ParameterTemplate.objects.create(
            name='Serial Number',
            description='A globally unique parameter',
            unique=common.models.ParameterTemplate.UniqueOptions.GLOBAL,
        )

        common.models.Parameter.objects.create(
            template=normal_template,
            model_type=part_a.get_content_type(),
            model_id=part_a.pk,
            data='Red',
        )

        common.models.Parameter.objects.create(
            template=unique_template,
            model_type=part_a.get_content_type(),
            model_id=part_a.pk,
            data='ABC123',
        )

        # Copy parameters from part_a to part_b
        part_b.copy_parameters_from(part_a)

        # The non-unique parameter should have been copied
        self.assertEqual(part_b.get_parameter('Color').data, 'Red')

        # The unique parameter should *not* have been copied, to avoid a conflicting value
        self.assertIsNone(part_b.get_parameter('Serial Number'))

    def test_parameter_annotation(self):
        """Test that we can annotate parameters against a queryset."""
        from company.models import Company

        templates = []
        parameters = []
        companies = []

        for ii in range(100):
            company = Company(
                name=f'Test Company {ii}',
                description='A company for testing parameter annotations',
            )
            companies.append(company)

        Company.objects.bulk_create(companies)

        # Let's create a large number of parameters
        for ii in range(25):
            templates.append(
                common.models.ParameterTemplate(
                    name=f'Test Parameter {ii}',
                    units='',
                    description='A parameter for testing annotations',
                    model_type=Company.get_content_type(),
                    enabled=True,
                )
            )

        common.models.ParameterTemplate.objects.bulk_create(templates)

        # Create a parameter for every company against every template
        for company in Company.objects.all():
            for template in common.models.ParameterTemplate.objects.all():
                parameters.append(
                    common.models.Parameter(
                        template=template,
                        model_type=company.get_content_type(),
                        model_id=company.pk,
                        data=f'Test data for {company.name} - {template.name}',
                    )
                )

        common.models.Parameter.objects.bulk_create(parameters)

        self.assertEqual(
            common.models.Parameter.objects.count(), len(companies) * len(templates)
        )

        # We will fetch the companies, annotated with all parameters
        url = reverse('api-company-list')

        # By default, we do not expect any parameter annotations
        response = self.get(url, data={'limit': 5})

        self.assertEqual(response.data['count'], len(companies))
        for company in response.data['results']:
            self.assertNotIn('parameters', company)

        # Fetch all companies, explicitly without parameters
        with self.assertNumQueriesLessThan(20):
            response = self.get(url, data={'parameters': False})

        # Now, annotate with parameters
        # This must be done efficiently, without an 1 + N query pattern
        with self.assertNumQueriesLessThan(45):
            response = self.get(url, data={'parameters': True})

        self.assertEqual(len(response.data), len(companies))

        for company in response.data:
            self.assertIn('parameters', company)
            self.assertEqual(
                len(company['parameters']),
                len(templates),
                'Incorrect number of parameter annotations found',
            )

    def test_parameter_delete(self):
        """Test that associated parameters are correctly deleted when removing the linked model."""
        from part.models import Part

        part = Part.objects.create(
            name='Test Part', description='A part for testing', active=False
        )

        # Create a ParameterTemplate for the Part model
        template = common.models.ParameterTemplate.objects.create(
            name='Test Parameter',
            description='A parameter template for testing parameter deletion',
            model_type=None,
        )

        # Create a Parameter for the Build
        parameter = common.models.Parameter.objects.create(
            template=template,
            model_type=part.get_content_type(),
            model_id=part.pk,
            data='Test data',
        )

        self.assertTrue(
            common.models.Parameter.objects.filter(pk=parameter.pk).exists()
        )

        N = common.models.Parameter.objects.count()

        # Now delete the part instance
        self.assignRole('part.delete')
        self.delete(
            reverse('api-part-detail', kwargs={'pk': part.pk}), expected_code=204
        )

        self.assertEqual(common.models.Parameter.objects.count(), N - 1)
        self.assertFalse(
            common.models.Parameter.objects.filter(template=template.pk).exists()
        )


class AttachmentAPITests(InvenTreeAPITestCase):
    """Tests for the Attachment API."""

    def test_attachments(self):
        """Test API functionality for attachments."""
        from common.models import Attachment
        from part.models import Part

        self.assignRole('part.add')

        part = Part.objects.create(name='Test Part', description='A part for testing')

        N = Attachment.objects.count()

        # Upload multiple attachments against the part instance
        for ii in range(5):
            file_object = io.StringIO('Hello world')
            file_object.seek(0)

            fn = f'test_file_{ii}.txt'

            content_file = ContentFile(file_object.read(), name=fn)

            url = reverse('api-attachment-list')

            response = self.post(
                url,
                data={
                    'model_type': 'part',
                    'model_id': part.pk,
                    'attachment': content_file,
                    'comment': f'This is test file {ii}',
                },
                format='multipart',
                expected_code=201,
            )

            data = response.data

            # Check that the file has actually been created
            self.assertEqual(data['filename'], fn)
            self.assertTrue(
                default_storage.exists(data['attachment'].replace('/media/', ''))
            )

        # Check that we have the expected number of attachments
        self.assertEqual(Attachment.objects.count(), N + 5)
        self.assertEqual(part.attachments.count(), 5)

        # Let's rename one of the attachments
        att = part.attachments.first()
        self.assertEqual(att.basename, 'test_file_0.txt')

        url = reverse('api-attachment-detail', kwargs={'pk': att.pk})

        # A few failed attempts
        for new_name in [
            'different_ext.docx',
            'test_file_1.txt',
            '../../test_file.txt',
        ]:
            print('- ATTEMPTING:', new_name)
            response = self.patch(url, data={'filename': new_name}, expected_code=400)

        att.refresh_from_db()
        self.assertEqual(att.basename, 'test_file_0.txt')

        # Let's try seriously this time
        new_name = 'a_new_file.txt'
        response = self.patch(url, data={'filename': new_name}, expected_code=200)

        att.refresh_from_db()
        self.assertEqual(att.basename, new_name)

        # Check that the file has been renamed on disk
        self.assertTrue(
            default_storage.exists(f'attachments/part/{part.pk}/{new_name}')
        )
        self.assertFalse(
            default_storage.exists(f'attachments/part/{part.pk}/test_file_0.txt')
        )

        # Next, let's delete the attachment manually - via the API
        response = self.delete(url, expected_code=403)
        self.assignRole('part.delete')
        response = self.delete(url, expected_code=204)

        # Check that the file has been deleted from disk
        self.assertFalse(
            default_storage.exists(f'attachments/part/{part.pk}/{new_name}')
        )

        self.assertEqual(Attachment.objects.count(), N + 4)
        self.assertEqual(part.attachments.count(), 4)

        # Fetch the remaining attachments
        attachments = list(part.attachments.all())

        # Now, delete the part instance
        part.active = False
        part.save()
        part.delete()

        self.assertEqual(Attachment.objects.count(), N)

        for att in attachments:
            # Ensure that the file associated with each attachment has been removed
            self.assertFalse(default_storage.exists(att.attachment.path))


class AttachmentThumbnailAPITests(InvenTreeAPITestCase):
    """Tests for thumbnail generation when uploading attachments via the API."""

    def setUp(self):
        """Set up a Part instance and required roles."""
        from part.models import Part

        super().setUp()
        self.assignRole('part.add')
        self.assignRole('part.delete')
        self.part = Part.objects.create(
            name='Thumbnail Test Part', description='Part for thumbnail testing'
        )

    def _make_image_file(self, name='test.png', size=(100, 100), color='red'):
        """Return a SimpleUploadedFile containing a valid PNG image."""
        buf = io.BytesIO()
        Image.new('RGB', size, color=color).save(buf, format='PNG')
        return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')

    def _upload_attachment(self, file_obj, expected_code=201):
        """Upload a file attachment against the test part and return the response."""
        return self.post(
            reverse('api-attachment-list'),
            data={
                'model_type': 'part',
                'model_id': self.part.pk,
                'attachment': file_obj,
            },
            format='multipart',
            expected_code=expected_code,
        )

    def test_thumbnail_valid_image(self):
        """Uploading a valid image file should set is_image=True and generate a thumbnail."""
        from common.models import Attachment

        response = self._upload_attachment(self._make_image_file())
        att = Attachment.objects.get(pk=response.data['pk'])

        self.assertTrue(att.is_image)
        self.assertTrue(att.thumbnail)
        self.assertTrue(default_storage.exists(att.thumbnail.name))

    def test_thumbnail_invalid_image(self):
        """Uploading a file with an image extension but invalid image data should not create a thumbnail."""
        from common.models import Attachment

        bad_file = SimpleUploadedFile(
            'corrupt.png', b'this is not image data', content_type='image/png'
        )
        response = self._upload_attachment(bad_file)
        att = Attachment.objects.get(pk=response.data['pk'])

        self.assertFalse(att.is_image)
        self.assertFalse(att.thumbnail)

    def test_thumbnail_non_image_file(self):
        """Uploading a non-image file should leave is_image=False with no thumbnail."""
        from common.models import Attachment

        txt_file = SimpleUploadedFile(
            'document.txt', b'Hello, InvenTree!', content_type='text/plain'
        )
        response = self._upload_attachment(txt_file)
        att = Attachment.objects.get(pk=response.data['pk'])

        self.assertFalse(att.is_image)
        self.assertFalse(att.thumbnail)

    def test_thumbnail_large_image(self):
        """A large image attachment should produce a thumbnail no larger than THUMBNAIL_SIZE on each side."""
        from common.models import Attachment

        response = self._upload_attachment(self._make_image_file(size=(1000, 1000)))
        att = Attachment.objects.get(pk=response.data['pk'])

        self.assertTrue(att.is_image)
        self.assertTrue(att.thumbnail)

        thumb_data = default_storage.open(att.thumbnail.name).read()
        thumb_img = Image.open(io.BytesIO(thumb_data))
        self.assertLessEqual(thumb_img.width, Attachment.THUMBNAIL_SIZE)
        self.assertLessEqual(thumb_img.height, Attachment.THUMBNAIL_SIZE)

    def test_thumbnail_deleted_with_attachment(self):
        """Deleting an attachment via the API should also remove its thumbnail from storage."""
        from common.models import Attachment

        response = self._upload_attachment(self._make_image_file())
        att = Attachment.objects.get(pk=response.data['pk'])

        self.assertTrue(att.thumbnail)
        thumb_name = att.thumbnail.name
        att_name = att.attachment.name

        self.assertTrue(default_storage.exists(att_name))
        self.assertTrue(default_storage.exists(thumb_name))

        self.delete(
            reverse('api-attachment-detail', kwargs={'pk': att.pk}), expected_code=204
        )

        self.assertFalse(default_storage.exists(att_name))
        self.assertFalse(default_storage.exists(thumb_name))

    def test_thumbnail_zero_byte_file(self):
        """Uploading a zero-byte file should be rejected by Django's file validation before reaching thumbnail logic."""
        empty_file = SimpleUploadedFile('empty.png', b'', content_type='image/png')
        # Django's FileField rejects empty uploads at the serializer/validation layer
        response = self._upload_attachment(empty_file, expected_code=400)
        self.assertIn('attachment', response.data)

    def test_thumbnail_link_attachment(self):
        """An attachment created with an external link (no file) should not generate a thumbnail."""
        from common.models import Attachment

        response = self.post(
            reverse('api-attachment-list'),
            data={
                'model_type': 'part',
                'model_id': self.part.pk,
                'link': 'https://example.com/some/resource',
            },
            format='multipart',
            expected_code=201,
        )

        att = Attachment.objects.get(pk=response.data['pk'])

        self.assertFalse(att.is_image)
        self.assertFalse(att.thumbnail)

    def test_is_image_filter(self):
        """The is_image filter on the attachment list endpoint should return only matching attachments."""
        url = reverse('api-attachment-list')
        base_filters = {'model_type': 'part', 'model_id': self.part.pk}

        # Upload one valid image and three non-image attachments
        self._upload_attachment(self._make_image_file('img1.png'))
        self._upload_attachment(
            SimpleUploadedFile(
                'corrupt.png', b'not image data', content_type='image/png'
            )
        )
        self._upload_attachment(
            SimpleUploadedFile('doc.txt', b'hello', content_type='text/plain')
        )
        self.post(
            url,
            data={**base_filters, 'link': 'https://example.com/resource'},
            format='multipart',
            expected_code=201,
        )

        all_attachments = self.get(url, base_filters, expected_code=200).data
        self.assertEqual(len(all_attachments), 4)

        # is_image=true → only the valid image
        images = self.get(
            url, {**base_filters, 'is_image': 'true'}, expected_code=200
        ).data
        self.assertEqual(len(images), 1)
        self.assertTrue(images[0]['is_image'])

        # is_image=false → the three non-image attachments
        non_images = self.get(
            url, {**base_filters, 'is_image': 'false'}, expected_code=200
        ).data
        self.assertEqual(len(non_images), 3)
        self.assertTrue(all(not a['is_image'] for a in non_images))

    def test_upload_exceeds_size_limit(self):
        """Uploading a file that exceeds INVENTREE_UPLOAD_MAX_SIZE should be rejected with a 400 error."""
        from common.settings import get_global_setting, set_global_setting

        original_limit = get_global_setting('INVENTREE_UPLOAD_MAX_SIZE')
        # Use a 1 MB ceiling so the test file stays small and fast
        set_global_setting('INVENTREE_UPLOAD_MAX_SIZE', 1, change_user=None)

        limit_bytes = 1 * 1024 * 1024

        try:
            # File exactly at the limit — validator uses >, so this must be accepted
            self._upload_attachment(
                SimpleUploadedFile(
                    'at_limit.txt', b'\x00' * limit_bytes, content_type='text/plain'
                ),
                expected_code=201,
            )

            # File one byte over the limit — must be rejected
            response = self._upload_attachment(
                SimpleUploadedFile(
                    'over_limit.txt',
                    b'\x00' * (limit_bytes + 1),
                    content_type='text/plain',
                ),
                expected_code=400,
            )
            self.assertIn('attachment', response.data)
        finally:
            set_global_setting(
                'INVENTREE_UPLOAD_MAX_SIZE', original_limit, change_user=None
            )


class TagAPITests(InvenTreeAPITestCase):
    """Tests for the Tag API endpoints and tag-based filtering."""

    roles = 'all'

    LIST_URL = 'api-tag-list'
    DETAIL_URL = 'api-tag-detail'

    def setUp(self):
        """Create a small set of tagged objects for filter testing."""
        super().setUp()

        from part.models import Part

        self.part_a = Part.objects.create(
            name='Tagged Part A', description='Part with apple and banana tags'
        )
        self.part_b = Part.objects.create(
            name='Tagged Part B', description='Part with apple tag only'
        )
        self.part_c = Part.objects.create(
            name='Untagged Part C', description='Part with no tags'
        )

        self.part_a.tags.add('apple', 'banana')
        self.part_b.tags.add('apple')

    # ------------------------------------------------------------------
    # Tag list / CRUD
    # ------------------------------------------------------------------

    def test_tag_list(self):
        """Tag list endpoint should return all existing tags."""
        url = reverse(self.LIST_URL)
        response = self.get(url)

        names = {t['name'] for t in response.data}
        self.assertIn('apple', names)
        self.assertIn('banana', names)

    def test_tag_create(self):
        """Staff users should be able to create tags via POST."""
        url = reverse(self.LIST_URL)
        n = Tag.objects.count()

        response = self.post(url, {'name': 'cherry'}, expected_code=201)
        self.assertEqual(response.data['name'], 'cherry')
        self.assertEqual(Tag.objects.count(), n + 1)

    def test_tag_create_non_staff(self):
        """Non-staff users must not be able to create tags."""
        self.user.is_staff = False
        self.user.save()

        url = reverse(self.LIST_URL)
        self.post(url, {'name': 'forbidden'}, expected_code=403)

    def test_tag_edit(self):
        """Staff users should be able to rename a tag via PATCH."""
        tag = Tag.objects.get(name='banana')
        url = reverse(self.DETAIL_URL, kwargs={'pk': tag.pk})

        response = self.patch(url, {'name': 'blueberry'}, expected_code=200)
        self.assertEqual(response.data['name'], 'blueberry')

        tag.refresh_from_db()
        self.assertEqual(tag.name, 'blueberry')

    def test_tag_delete(self):
        """Staff users should be able to delete a tag."""
        tag = Tag.objects.get(name='banana')
        url = reverse(self.DETAIL_URL, kwargs={'pk': tag.pk})

        self.delete(url, expected_code=204)
        self.assertFalse(Tag.objects.filter(name='banana').exists())

    def test_tag_search(self):
        """The list endpoint should support free-text search."""
        url = reverse(self.LIST_URL)

        response = self.get(url, data={'search': 'app'})
        names = [t['name'] for t in response.data]
        self.assertIn('apple', names)
        self.assertNotIn('banana', names)

    # ------------------------------------------------------------------
    # Filter by model type
    # ------------------------------------------------------------------

    def test_tag_filter_model_type(self):
        """Tags applied to a given model type should be returned when filtering by model_type."""
        url = reverse(self.LIST_URL)

        # Filter for tags applied to Part objects
        response = self.get(url, data={'model_type': 'part.part'})
        names = {t['name'] for t in response.data}

        self.assertIn('apple', names)
        self.assertIn('banana', names)

    def test_tag_filter_model_type_unrelated(self):
        """Filtering by a model type that has no tagged objects should return an empty list."""
        url = reverse(self.LIST_URL)

        # StockItem has no tagged objects in this test
        response = self.get(url, data={'model_type': 'stock.stockitem'})
        self.assertEqual(len(response.data), 0)

    def test_tag_filter_model_type_invalid(self):
        """An unrecognised model_type value should return a 400 error."""
        url = reverse(self.LIST_URL)
        self.get(url, data={'model_type': 'notanapp.notamodel'}, expected_code=400)

    # ------------------------------------------------------------------
    # Filter Part list by tags
    # ------------------------------------------------------------------

    def test_part_filter_single_tag(self):
        """Filtering parts by a single tag should return only parts with that tag."""
        url = reverse('api-part-list')

        response = self.get(url, data={'tags': 'apple'})
        pks = {p['pk'] for p in response.data}

        self.assertIn(self.part_a.pk, pks)
        self.assertIn(self.part_b.pk, pks)
        self.assertNotIn(self.part_c.pk, pks)

    def test_part_filter_multiple_tags_and(self):
        """Filtering by comma-separated tags should return only parts that have ALL tags."""
        url = reverse('api-part-list')

        response = self.get(url, data={'tags': 'apple,banana'})
        pks = {p['pk'] for p in response.data}

        self.assertIn(self.part_a.pk, pks)
        self.assertNotIn(self.part_b.pk, pks)  # only has 'apple'
        self.assertNotIn(self.part_c.pk, pks)  # no tags at all

    def test_part_filter_tag_case_insensitive(self):
        """Tag filtering should be case-insensitive."""
        url = reverse('api-part-list')

        response = self.get(url, data={'tags': 'APPLE'})
        pks = {p['pk'] for p in response.data}

        self.assertIn(self.part_a.pk, pks)
        self.assertIn(self.part_b.pk, pks)

    def test_part_filter_nonexistent_tag(self):
        """Filtering by a tag that no part has should return an empty result set."""
        url = reverse('api-part-list')

        response = self.get(url, data={'tags': 'doesnotexist'})
        self.assertEqual(len(response.data), 0)

    def test_part_filter_tag_whitespace(self):
        """Whitespace around comma-separated tag names should be ignored."""
        url = reverse('api-part-list')

        response = self.get(url, data={'tags': ' apple , banana '})
        pks = {p['pk'] for p in response.data}

        self.assertIn(self.part_a.pk, pks)
        self.assertNotIn(self.part_b.pk, pks)


class SelectionListLockedTest(InvenTreeAPITestCase):
    """Tests that a locked SelectionList rejects all entry mutations."""

    def setUp(self):
        """Create a locked SelectionList with one entry."""
        super().setUp()

        self.sel_list = SelectionList.objects.create(name='Locked List', locked=True)
        self.entry = SelectionListEntry.objects.create(
            list=self.sel_list, value='v1', label='Entry 1'
        )

        self.list_url = reverse(
            'api-selectionlist-detail', kwargs={'pk': self.sel_list.pk}
        )
        self.entry_list_url = reverse(
            'api-selectionlistentry-list', kwargs={'pk': self.sel_list.pk}
        )
        self.entry_detail_url = reverse(
            'api-selectionlistentry-detail',
            kwargs={'pk': self.sel_list.pk, 'entrypk': self.entry.pk},
        )

    def test_create_entry_locked(self):
        """POST a new entry to a locked list should be rejected."""
        response = self.post(
            self.entry_list_url,
            {'list': self.sel_list.pk, 'value': 'v2', 'label': 'Entry 2'},
            expected_code=400,
        )
        self.assertIn('list', response.data)
        self.assertIn('locked', str(response.data['list']).lower())

    def test_update_entry_locked(self):
        """PATCH an entry on a locked list should be rejected."""
        response = self.patch(
            self.entry_detail_url, {'label': 'Changed'}, expected_code=400
        )
        self.assertIn('list', response.data)
        self.assertIn('locked', str(response.data['list']).lower())

    def test_delete_entry_locked(self):
        """DELETE an entry from a locked list should be rejected."""
        self.delete(self.entry_detail_url, expected_code=403)
        self.assertTrue(SelectionListEntry.objects.filter(pk=self.entry.pk).exists())

    def test_patch_list_with_choices_locked(self):
        """PATCH the list with a choices payload should be rejected when locked."""
        response = self.patch(
            self.list_url,
            {'choices': [{'value': 'v2', 'label': 'New'}]},
            expected_code=400,
        )
        self.assertIn('locked', response.data)

    def test_patch_list_without_choices_preserves_entries(self):
        """PATCH the list without choices should not touch entries (even when unlocked)."""
        self.sel_list.locked = False
        self.sel_list.save()

        self.patch(self.list_url, {'name': 'Renamed List'}, expected_code=200)

        # Entry must still exist — omitting choices must not delete entries
        self.assertTrue(SelectionListEntry.objects.filter(pk=self.entry.pk).exists())
