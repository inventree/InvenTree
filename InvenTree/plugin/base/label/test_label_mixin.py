"""Unit tests for the label printing mixin"""

from django.apps import apps
from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase
from label.models import PartLabel, StockItemLabel, StockLocationLabel
from part.models import Part
from plugin.registry import registry
from stock.models import StockItem, StockLocation


class LabelMixinTests(InvenTreeAPITestCase):
    """Test that the Label mixin operates correctly"""

    fixtures = [
        'category',
        'part',
        'location',
        'stock',
    ]

    roles = 'all'

    def activate_plugin(self):
        """Activate the 'samplelabel' plugin"""

        config = registry.get_plugin('samplelabel').plugin_config()
        config.active = True
        config.save()

    def get_url(self, parts, plugin_ref, label, url_name: str = 'api-part-label-print', url_single: str = 'part'):
        """Generate an URL to print a label"""
        # Gather part details
        if len(parts) == 1:
            part_url = f'{url_single}={parts[0].pk}'
        else:
            part_url = '&'.join([f'{url_single}s={item.pk}' for item in parts])
        # Construct url
        url = f'{reverse(url_name, kwargs={"pk": label.pk})}?{part_url}'
        if plugin_ref:
            url += f'&plugin={plugin_ref}'
        return url

    def test_installed(self):
        """Test that the sample printing plugin is installed"""

        # Get all label plugins
        plugins = registry.with_mixin('labels')
        self.assertEqual(len(plugins), 1)

        # But, it is not 'active'
        plugins = registry.with_mixin('labels', active=True)
        self.assertEqual(len(plugins), 0)

    def test_api(self):
        """Test that we can filter the API endpoint by mixin"""

        url = reverse('api-plugin-list')

        # Try POST (disallowed)
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 405)

        response = self.client.get(
            url,
            {
                'mixin': 'labels',
                'active': True,
            }
        )

        # No results matching this query!
        self.assertEqual(len(response.data), 0)

        # What about inactive?
        response = self.client.get(
            url,
            {
                'mixin': 'labels',
                'active': False,
            }
        )

        self.assertEqual(len(response.data), 0)

        self.activate_plugin()
        # Should be available via the API now
        response = self.client.get(
            url,
            {
                'mixin': 'labels',
                'active': True,
            }
        )

        self.assertEqual(len(response.data), 1)
        data = response.data[0]
        self.assertEqual(data['key'], 'samplelabel')

    def test_printing_process(self):
        """Test that a label can be printed"""

        # Ensure the labels were created
        apps.get_app_config('label').create_labels()

        # Lookup references
        part = Part.objects.first()
        plugin_ref = 'samplelabel'
        label = PartLabel.objects.first()

        url = self.get_url([part], plugin_ref, label)

        # Non-exsisting plugin
        response = self.get(f'{url}123', expected_code=404)
        self.assertIn(f'Plugin \'{plugin_ref}123\' not found', str(response.content, 'utf8'))

        # Inactive plugin
        response = self.get(url, expected_code=400)
        self.assertIn(f'Plugin \'{plugin_ref}\' is not enabled', str(response.content, 'utf8'))

        # Active plugin
        self.activate_plugin()

        # Print one part
        self.get(url, expected_code=200)

        # Print multiple parts
        self.get(self.get_url(Part.objects.all()[:2], plugin_ref, label), expected_code=200)

        # Print multiple parts without a plugin
        self.get(self.get_url(Part.objects.all()[:2], None, label), expected_code=200)

    def test_printing_endpoints(self):
        """Cover the endpoints not covered by `test_printing_process`"""
        plugin_ref = 'samplelabel'

        # Activate the label components
        apps.get_app_config('label').create_labels()
        self.activate_plugin()

        def run_print_test(label, qs, url_name, url_single):
            """Run tests on single and multiple page printing

            Args:
                label (_type_): class of the label
                qs (_type_): class of the base queryset
                url_name (_type_): url for printing endpoint
                url_single (_type_): item lookup reference
            """
            label = label.objects.first()
            qs = qs.objects.all()

            # Single page printing
            self.get(self.get_url(qs[:1], plugin_ref, label, url_name, url_single), expected_code=200)

            # Multi page printing
            self.get(self.get_url(qs[:2], plugin_ref, label, url_name, url_single), expected_code=200)

        # Test StockItemLabels
        run_print_test(StockItemLabel, StockItem, 'api-stockitem-label-print', 'item')

        # Test StockLocationLabels
        run_print_test(StockLocationLabel, StockLocation, 'api-stocklocation-label-print', 'location')
