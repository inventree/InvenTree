"""Unit tests for label API."""

import json
from io import StringIO

from django.core.cache import cache
from django.urls import reverse

import label.models as label_models
from build.models import BuildLine
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from stock.models import StockItem, StockLocation


class LabelTest(InvenTreeAPITestCase):
    """Base class for unit testing label model API endpoints."""

    fixtures = ['category', 'part', 'location', 'stock', 'bom', 'build']

    superuser = True

    model = None
    list_url = None
    detail_url = None
    metadata_url = None

    print_url = None
    print_itemname = None
    print_itemmodel = None

    def setUp(self):
        """Ensure cache is cleared as part of test setup."""
        cache.clear()
        return super().setUp()

    def test_api_url(self):
        """Test returned API Url against URL tag defined in this file."""
        if not self.list_url:
            return

        self.assertEqual(reverse(self.list_url), self.model.get_api_url())

    def test_list_endpoint(self):
        """Test that the LIST endpoint works for each model."""
        if not self.list_url:
            return

        url = reverse(self.list_url)

        response = self.get(url)
        self.assertEqual(response.status_code, 200)

        labels = self.model.objects.all()
        n = len(labels)

        # API endpoint must return correct number of reports
        self.assertEqual(len(response.data), n)

        # Filter by "enabled" status
        response = self.get(url, {'enabled': True})
        self.assertEqual(len(response.data), n)

        response = self.get(url, {'enabled': False})
        self.assertEqual(len(response.data), 0)

        # Disable each report
        for label in labels:
            label.enabled = False
            label.save()

        # Filter by "enabled" status
        response = self.get(url, {'enabled': True})
        self.assertEqual(len(response.data), 0)

        response = self.get(url, {'enabled': False})
        self.assertEqual(len(response.data), n)

    def test_create_endpoint(self):
        """Test that creating a new report works for each label."""
        if not self.list_url:
            return

        url = reverse(self.list_url)

        # Create a new label
        # Django REST API "APITestCase" does not work like requests - to send a file without it existing on disk,
        # create it as a StringIO object, and upload it under parameter template
        filestr = StringIO(
            '{% extends "label/label_base.html" %}{% block content %}<pre>TEST LABEL</pre>{% endblock content %}'
        )
        filestr.name = 'ExampleTemplate.html'

        response = self.post(
            url,
            data={
                'name': 'New label',
                'description': 'A fancy new label created through API test',
                'label': filestr,
            },
            format=None,
            expected_code=201,
        )

        # Make sure the expected keys are in the response
        self.assertIn('pk', response.data)
        self.assertIn('name', response.data)
        self.assertIn('description', response.data)
        self.assertIn('label', response.data)
        self.assertIn('filters', response.data)
        self.assertIn('enabled', response.data)

        self.assertEqual(response.data['name'], 'New label')
        self.assertEqual(
            response.data['description'], 'A fancy new label created through API test'
        )
        self.assertEqual(response.data['label'].count('ExampleTemplate'), 1)

    def test_detail_endpoint(self):
        """Test that the DETAIL endpoint works for each label."""
        if not self.detail_url:
            return

        # Create an item first
        self.test_create_endpoint()

        labels = self.model.objects.all()

        n = len(labels)

        # Make sure at least one report defined
        self.assertGreaterEqual(n, 1)

        # Check detail page for first report
        response = self.get(
            reverse(self.detail_url, kwargs={'pk': labels[0].pk}), expected_code=200
        )

        # Make sure the expected keys are in the response
        self.assertIn('pk', response.data)
        self.assertIn('name', response.data)
        self.assertIn('description', response.data)
        self.assertIn('label', response.data)
        self.assertIn('filters', response.data)
        self.assertIn('enabled', response.data)

        filestr = StringIO(
            '{% extends "label/label_base.html" %}{% block content %}<pre>TEST LABEL</pre>{% endblock content %}'
        )
        filestr.name = 'ExampleTemplate_Updated.html'

        # Check PATCH method
        response = self.patch(
            reverse(self.detail_url, kwargs={'pk': labels[0].pk}),
            {
                'name': 'Changed name during test',
                'description': 'New version of the template',
                'label': filestr,
            },
            format=None,
            expected_code=200,
        )

        # Make sure the expected keys are in the response
        self.assertIn('pk', response.data)
        self.assertIn('name', response.data)
        self.assertIn('description', response.data)
        self.assertIn('label', response.data)
        self.assertIn('filters', response.data)
        self.assertIn('enabled', response.data)

        self.assertEqual(response.data['name'], 'Changed name during test')
        self.assertEqual(response.data['description'], 'New version of the template')

        self.assertEqual(response.data['label'].count('ExampleTemplate_Updated'), 1)

    def test_delete(self):
        """Test deleting, after other test are done."""
        if not self.detail_url:
            return

        # Create an item first
        self.test_create_endpoint()

        labels = self.model.objects.all()
        n = len(labels)
        # Make sure at least one label defined
        self.assertGreaterEqual(n, 1)

        # Delete the last report
        response = self.delete(
            reverse(self.detail_url, kwargs={'pk': labels[n - 1].pk}), expected_code=204
        )

    def test_print_label(self):
        """Test printing a label."""
        if not self.print_url:
            return

        # Create an item first
        self.test_create_endpoint()

        labels = self.model.objects.all()
        n = len(labels)
        # Make sure at least one label defined
        self.assertGreaterEqual(n, 1)

        url = reverse(self.print_url, kwargs={'pk': labels[0].pk})

        # Try to print without providing a valid item
        response = self.get(url, expected_code=400)

        # Try to print with an invalid item
        response = self.get(url, {self.print_itemname: 9999}, expected_code=400)

        # Now print with a valid item
        print(f'{self.print_itemmodel = }')
        print(f'{self.print_itemmodel.objects.all() = }')

        item = self.print_itemmodel.objects.first()
        self.assertIsNotNone(item)

        response = self.get(url, {self.print_itemname: item.pk}, expected_code=200)

        response_json = json.loads(response.content.decode('utf-8'))

        self.assertIn('file', response_json)
        self.assertIn('success', response_json)
        self.assertIn('message', response_json)
        self.assertTrue(response_json['success'])

    def test_metadata_endpoint(self):
        """Unit tests for the metadata field."""
        if not self.metadata_url:
            return

        # Create an item first
        self.test_create_endpoint()

        labels = self.model.objects.all()
        n = len(labels)
        # Make sure at least one label defined
        self.assertGreaterEqual(n, 1)

        # Test getting metadata
        response = self.get(
            reverse(self.metadata_url, kwargs={'pk': labels[0].pk}), expected_code=200
        )

        self.assertEqual(response.data, {'metadata': {}})


class TestStockItemLabel(LabelTest):
    """Unit testing class for the StockItemLabel model."""

    model = label_models.StockItemLabel

    list_url = 'api-stockitem-label-list'
    detail_url = 'api-stockitem-label-detail'
    metadata_url = 'api-stockitem-label-metadata'

    print_url = 'api-stockitem-label-print'
    print_itemname = 'item'
    print_itemmodel = StockItem


class TestStockLocationLabel(LabelTest):
    """Unit testing class for the StockLocationLabel model."""

    model = label_models.StockLocationLabel

    list_url = 'api-stocklocation-label-list'
    detail_url = 'api-stocklocation-label-detail'
    metadata_url = 'api-stocklocation-label-metadata'

    print_url = 'api-stocklocation-label-print'
    print_itemname = 'location'
    print_itemmodel = StockLocation


class TestPartLabel(LabelTest):
    """Unit testing class for the PartLabel model."""

    model = label_models.PartLabel

    list_url = 'api-part-label-list'
    detail_url = 'api-part-label-detail'
    metadata_url = 'api-part-label-metadata'

    print_url = 'api-part-label-print'
    print_itemname = 'part'
    print_itemmodel = Part


class TestBuildLineLabel(LabelTest):
    """Unit testing class for the BuildLine model."""

    model = label_models.BuildLineLabel

    list_url = 'api-buildline-label-list'
    detail_url = 'api-buildline-label-detail'
    metadata_url = 'api-buildline-label-metadata'

    print_url = 'api-buildline-label-print'
    print_itemname = 'line'
    print_itemmodel = BuildLine
