"""Tests for labels"""

import io
import json

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.urls import reverse

from common.models import InvenTreeSetting
from InvenTree.helpers import validateFilterString
from InvenTree.unit_test import InvenTreeAPITestCase
from label.models import LabelOutput
from part.models import Part
from plugin.registry import registry
from stock.models import StockItem

from .models import PartLabel, StockItemLabel, StockLocationLabel


class LabelTest(InvenTreeAPITestCase):
    """Unit test class for label models"""

    fixtures = ['category', 'part', 'location', 'stock']

    @classmethod
    def setUpTestData(cls):
        """Ensure that some label instances exist as part of init routine"""
        super().setUpTestData()
        apps.get_app_config('label').create_labels()

    def test_default_labels(self):
        """Test that the default label templates are copied across."""
        labels = StockItemLabel.objects.all()

        self.assertTrue(labels.count() > 0)

        labels = StockLocationLabel.objects.all()

        self.assertTrue(labels.count() > 0)

    def test_default_files(self):
        """Test that label files exist in the MEDIA directory."""

        def test_subdir(ref_name):
            item_dir = settings.MEDIA_ROOT.joinpath('label', 'inventree', ref_name)
            self.assertTrue(len([item_dir.iterdir()]) > 0)

        test_subdir('stockitem')
        test_subdir('stocklocation')
        test_subdir('part')

    def test_filters(self):
        """Test the label filters."""
        filter_string = 'part__pk=10'

        filters = validateFilterString(filter_string, model=StockItem)

        self.assertEqual(type(filters), dict)

        bad_filter_string = 'part_pk=10'

        with self.assertRaises(ValidationError):
            validateFilterString(bad_filter_string, model=StockItem)

    def test_label_rendering(self):
        """Test label rendering."""
        labels = PartLabel.objects.all()
        part = Part.objects.first()

        for label in labels:
            url = reverse('api-part-label-print', kwargs={'pk': label.pk})

            # Check that label printing returns the correct response type
            response = self.get(f'{url}?parts={part.pk}', expected_code=200)
            self.assertIsInstance(response, JsonResponse)
            data = json.loads(response.content)

            self.assertIn('message', data)
            self.assertIn('file', data)
            label_file = data['file']
            self.assertIn('/media/label/output/', label_file)

    def test_print_part_label(self):
        """Actually 'print' a label, and ensure that the correct information is contained."""
        label_data = """
        {% load barcode %}
        {% load report %}

        <html>
        <!-- Test that the part instance is supplied -->
        part: {{ part.pk }} - {{ part.name }}
        <!-- Test qr data -->
        data: {{ qr_data|safe }}
        <!-- Test InvenTree URL -->
        url: {{ qr_url|safe }}
        <!-- Test image URL generation -->
        image: {% part_image part width=128 %}
        <!-- Test InvenTree logo -->
        logo: {% logo_image %}
        </html>
        """

        buffer = io.StringIO()
        buffer.write(label_data)

        template = ContentFile(buffer.getvalue(), 'label.html')

        # Construct a label template
        label = PartLabel.objects.create(
            name='test', description='Test label', enabled=True, label=template
        )

        # Ensure we are in "debug" mode (so the report is generated as HTML)
        InvenTreeSetting.set_setting('REPORT_ENABLE', True, None)

        # Set the 'debug' setting for the plugin
        plugin = registry.get_plugin('inventreelabel')
        plugin.set_setting('DEBUG', True)

        # Print via the API (Note: will default to the builtin plugin if no plugin supplied)
        url = reverse('api-part-label-print', kwargs={'pk': label.pk})

        prt = Part.objects.first()
        part_pk = prt.pk
        part_name = prt.name

        response = self.get(f'{url}?parts={part_pk}', expected_code=200)
        data = json.loads(response.content)
        self.assertIn('file', data)

        # Find the generated file
        output = LabelOutput.objects.last()

        # Open the file and read data
        with open(output.label.path, 'r') as f:
            content = f.read()

        # Test that each element has been rendered correctly
        self.assertIn(f'part: {part_pk} - {part_name}', content)
        self.assertIn(f'data: {{"part": {part_pk}}}', content)
        self.assertIn(f'http://testserver/part/{part_pk}/', content)

        # Check that a encoded image has been generated
        self.assertIn('data:image/png;charset=utf-8;base64,', content)

    def test_metadata(self):
        """Unit tests for the metadata field."""
        for model in [StockItemLabel, StockLocationLabel, PartLabel]:
            p = model.objects.first()

            self.assertIsNone(p.get_metadata('test'))
            self.assertEqual(p.get_metadata('test', backup_value=123), 123)

            # Test update via the set_metadata() method
            p.set_metadata('test', 3)
            self.assertEqual(p.get_metadata('test'), 3)

            for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
                p.set_metadata(k, k)

            self.assertEqual(len(p.metadata.keys()), 4)
