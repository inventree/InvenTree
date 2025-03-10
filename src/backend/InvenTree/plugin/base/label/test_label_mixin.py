"""Unit tests for the label printing mixin."""

import json
import os
from unittest import mock

from django.apps import apps
from django.urls import reverse

from pdfminer.high_level import extract_text
from PIL import Image

from InvenTree.settings import BASE_DIR
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from plugin.base.label.mixins import LabelPrintingMixin
from plugin.helpers import MixinNotImplementedError
from plugin.plugin import InvenTreePlugin
from plugin.registry import registry
from report.models import LabelTemplate
from report.tests import PrintTestMixins
from stock.models import StockItem, StockLocation


class LabelMixinTests(PrintTestMixins, InvenTreeAPITestCase):
    """Test that the Label mixin operates correctly."""

    fixtures = ['category', 'part', 'location', 'stock']

    roles = 'all'
    plugin_ref = 'samplelabelprinter'

    @property
    def printing_url(self):
        """Return the label printing URL."""
        return reverse('api-label-print')

    def test_wrong_implementation(self):
        """Test that a wrong implementation raises an error."""

        class WrongPlugin(LabelPrintingMixin, InvenTreePlugin):
            pass

        with self.assertRaises(MixinNotImplementedError):
            plugin = WrongPlugin()
            plugin.print_label(filename='test')

    def test_installed(self):
        """Test that the sample printing plugin is installed."""
        # Get all label plugins
        plugins = registry.with_mixin('labels', active=None)
        self.assertEqual(len(plugins), 4)

        # But, it is not 'active'
        plugins = registry.with_mixin('labels', active=True)
        self.assertEqual(len(plugins), 3)

    def test_api(self):
        """Test that we can filter the API endpoint by mixin."""
        url = reverse('api-plugin-list')

        # Try POST (disallowed)
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 405)

        response = self.client.get(url, {'mixin': 'labels', 'active': True})

        # No results matching this query!
        self.assertEqual(len(response.data), 0)

        # What about inactive?
        response = self.client.get(url, {'mixin': 'labels', 'active': False})

        self.assertEqual(len(response.data), 0)

        self.do_activate_plugin()
        # Should be available via the API now
        response = self.client.get(url, {'mixin': 'labels', 'active': True})

        self.assertEqual(len(response.data), 4)

        labels = [item['key'] for item in response.data]

        self.assertIn('samplelabelprinter', labels)
        self.assertIn('inventreelabelsheet', labels)

    def test_printing_process(self):
        """Test that a label can be printed."""
        # Ensure the labels were created
        apps.get_app_config('report').create_default_labels()
        apps.get_app_config('report').create_default_reports()

        test_path = BASE_DIR / '_testfolder' / 'label'

        parts = Part.objects.all()[:2]

        template = LabelTemplate.objects.filter(enabled=True, model_type='part').first()

        self.assertIsNotNone(template)
        self.assertTrue(template.enabled)

        url = self.printing_url

        # Template does not exist
        response = self.post(
            url, {'template': 9999, 'plugin': 9999, 'items': []}, expected_code=400
        )

        self.assertIn('object does not exist', str(response.data['template']))
        self.assertIn('list may not be empty', str(response.data['items']))

        # Plugin is not a label plugin
        no_valid_plg = registry.get_plugin('digikeyplugin').plugin_config()

        response = self.post(
            url,
            {'template': template.pk, 'plugin': no_valid_plg.key, 'items': [1, 2, 3]},
            expected_code=400,
        )

        self.assertIn('Plugin does not support label printing', str(response.data))

        # Find available plugins
        plugins = registry.with_mixin('labels')
        self.assertGreater(len(plugins), 0)

        plugin = registry.get_plugin('samplelabelprinter')
        self.assertIsNotNone(plugin)
        config = plugin.plugin_config()

        # Ensure that the plugin is not active
        registry.set_plugin_state(plugin.slug, False)

        # Plugin is not active - should return error
        response = self.post(
            url,
            {'template': template.pk, 'plugin': config.key, 'items': [1, 2, 3]},
            expected_code=400,
        )
        self.assertIn('Plugin is not active', str(response.data['plugin']))

        # Active plugin
        self.do_activate_plugin()

        # Print one part
        response = self.post(
            url,
            {'template': template.pk, 'plugin': config.key, 'items': [parts[0].pk]},
            expected_code=201,
        )

        self.assertEqual(response.data['plugin'], 'samplelabelprinter')
        self.assertIsNone(response.data['output'])

        # Print multiple parts
        response = self.post(
            url,
            {
                'template': template.pk,
                'plugin': config.key,
                'items': [item.pk for item in parts],
            },
            expected_code=201,
        )

        self.assertEqual(response.data['plugin'], 'samplelabelprinter')
        self.assertIsNone(response.data['output'])

        # Print multiple parts without a plugin
        response = self.post(
            url,
            {'template': template.pk, 'items': [item.pk for item in parts]},
            expected_code=201,
        )

        self.assertEqual(response.data['plugin'], 'inventreelabel')
        self.assertIsNotNone(response.data['output'])

        data = json.loads(response.content)
        self.assertIn('output', data)

        # Print no part
        self.post(
            url,
            {'template': template.pk, 'plugin': plugin.pk, 'items': None},
            expected_code=400,
        )

        # Test that the labels have been printed
        # The sample labelling plugin simply prints to file
        self.assertTrue(os.path.exists(f'{test_path}.pdf'))

        # Read the raw .pdf data - ensure it contains some sensible information
        filetext = extract_text(f'{test_path}.pdf')
        matched = [part.name in filetext for part in parts]
        self.assertIn(True, matched)

        # Check that the .png file has already been created
        self.assertTrue(os.path.exists(f'{test_path}.png'))

        # And that it is a valid image file
        Image.open(f'{test_path}.png')

    def test_printing_options(self):
        """Test printing options."""
        # Ensure the labels were created
        apps.get_app_config('report').create_default_labels()

        # Lookup references
        parts = Part.objects.all()[:2]
        template = LabelTemplate.objects.filter(enabled=True, model_type='part').first()
        self.do_activate_plugin()
        plugin = registry.get_plugin(self.plugin_ref)

        # test options response
        options = self.options(
            self.printing_url, data={'plugin': plugin.slug}, expected_code=200
        ).json()
        self.assertIn('amount', options['actions']['POST'])

        with mock.patch.object(plugin, 'print_label') as print_label:
            # wrong value type
            res = self.post(
                self.printing_url,
                {
                    'plugin': plugin.slug,
                    'template': template.pk,
                    'items': [a.pk for a in parts],
                    'amount': '-no-valid-int-',
                },
                expected_code=400,
            ).json()
            self.assertIn('amount', res)
            print_label.assert_not_called()

            # correct value type
            self.post(
                self.printing_url,
                {
                    'template': template.pk,
                    'plugin': plugin.slug,
                    'items': [a.pk for a in parts],
                    'amount': 13,
                },
                expected_code=201,
            ).json()
            self.assertEqual(
                print_label.call_args.kwargs['printing_options'], {'amount': 13}
            )

    def test_printing_endpoints(self):
        """Cover the endpoints not covered by `test_printing_process`."""
        # Activate the label components
        apps.get_app_config('report').create_default_labels()
        self.do_activate_plugin()

        # Test StockItemLabel
        self.run_print_test(StockItem, 'stockitem')

        # Test StockLocationLabel
        self.run_print_test(StockLocation, 'stocklocation')

        # Test PartLabel
        self.run_print_test(Part, 'part')
