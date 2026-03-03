"""API unit tests for InvenTree common functionality."""

from django.urls import reverse

import common.models
from InvenTree.unit_test import InvenTreeAPITestCase


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
