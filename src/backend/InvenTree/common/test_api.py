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

    def test_create_template(self):
        """Test creation of a ParameterTemplate via the API."""
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
