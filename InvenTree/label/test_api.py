"""Unit tests for label API."""

from io import StringIO

from django.core.cache import cache
from django.urls import reverse

import label.models as label_models
from InvenTree.unit_test import InvenTreeAPITestCase


class LabelTest(InvenTreeAPITestCase):
    """Base class for unit testing label model API endpoints."""

    fixtures = ['part', 'location', 'stock']

    # superuser = True

    model = None
    list_url = None
    detail_url = None
    print_url = None

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

        reports = self.model.objects.all()

        n = len(reports)
        # API endpoint must return correct number of reports
        self.assertEqual(len(response.data), n)

        # Filter by "enabled" status
        response = self.get(url, {'enabled': True})
        self.assertEqual(len(response.data), n)

        response = self.get(url, {'enabled': False})
        self.assertEqual(len(response.data), 0)

        # Disable each report
        for report in reports:
            report.enabled = False
            report.save()

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
            '{% extends "label/label_base.html" %}<pre>TEST LABEL</pre>{% endblock content %}'
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
        self.assertIn('template', response.data)
        self.assertIn('filters', response.data)
        self.assertIn('enabled', response.data)

        self.assertEqual(response.data['name'], 'New label')
        self.assertEqual(
            response.data['description'], 'A fancy new label created through API test'
        )
        self.assertTrue(response.data['template'].endswith('ExampleTemplate.html'))

    def test_detail_endpoint(self):
        """Test that the DETAIL endpoint works for each report."""
        if not self.detail_url:
            return

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
        self.assertIn('template', response.data)
        self.assertIn('filters', response.data)
        self.assertIn('enabled', response.data)

        filestr = StringIO(
            '{% extends "label/label_base.html" %}<pre>TEST LABEL</pre>{% endblock content %}'
        )
        filestr.name = 'ExampleTemplate_Updated.html'

        # Check PATCH method
        response = self.patch(
            reverse(self.detail_url, kwargs={'pk': labels[0].pk}),
            {
                'name': 'Changed name during test',
                'description': 'New version of the template',
                'template': filestr,
            },
            format=None,
            expected_code=200,
        )

        # Make sure the expected keys are in the response
        self.assertIn('pk', response.data)
        self.assertIn('name', response.data)
        self.assertIn('description', response.data)
        self.assertIn('template', response.data)
        self.assertIn('filters', response.data)
        self.assertIn('enabled', response.data)

        self.assertEqual(response.data['name'], 'Changed name during test')
        self.assertEqual(response.data['description'], 'New version of the template')

        self.assertTrue(
            response.data['template'].endswith('ExampleTemplate_Updated.html')
        )

        # Delete the last report
        response = self.delete(
            reverse(self.detail_url, kwargs={'pk': labels[n - 1].pk}), expected_code=204
        )

    def test_metadata_endpoint(self):
        """Unit tests for the metadata field."""
        if not self.metadata_url:
            return

        p = self.model.objects.first()

        self.assertEqual(p.metadata, {})

        self.assertIsNone(p.get_metadata('test'))
        self.assertEqual(p.get_metadata('test', backup_value=123), 123)

        # Test update via the set_metadata() method
        p.set_metadata('test', 3)
        self.assertEqual(p.get_metadata('test'), 3)

        for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
            p.set_metadata(k, k)

        self.assertEqual(len(p.metadata.keys()), 4)


class TestStockItemLabel(LabelTest):
    """Unit testing class for the StockItemLabel model."""

    model = label_models.StockItemLabel

    list_url = 'api-stockitem-label-list'
    detail_url = 'api-stockitem-label-detail'
    print_url = 'api-stockitem-label-print'
    metadata_url = 'api-stockitem-label-metadata'


class TestStockLocationLabel(LabelTest):
    """Unit testing class for the StockLocationLabel model."""

    model = label_models.StockLocationLabel

    list_url = 'api-stocklocation-label-list'
    detail_url = 'api-stocklocation-label-detail'
    print_url = 'api-stocklocation-label-print'
    metadata_url = 'api-stocklocation-label-metadata'


class TestPartLabel(LabelTest):
    """Unit testing class for the PartLabel model."""

    model = label_models.PartLabel

    list_url = 'api-part-label-list'
    detail_url = 'api-part-label-detail'
    print_url = 'api-part-label-print'
    metadata_url = 'api-part-label-metadata'
