"""Unit tests for the label printing mixin"""

from django.apps import apps
from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase
from label.models import PartLabel, StockItemLabel, StockLocationLabel
from part.models import Part
from plugin.base.label.mixins import LabelPrintingMixin
from plugin.helpers import MixinNotImplementedError
from plugin.plugin import InvenTreePlugin
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

    def do_activate_plugin(self):
        """Activate the 'samplelabel' plugin"""

        config = registry.get_plugin('samplelabel').plugin_config()
        config.active = True
        config.save()

    def do_url(self, parts, plugin_ref, label, url_name: str = 'api-part-label-print', url_single: str = 'part', invalid: bool = False):
        """Generate an URL to print a label"""
        # Construct URL
        kwargs = {}
        if label:
            kwargs["pk"] = label.pk

        url = reverse(url_name, kwargs=kwargs)

        # Append part filters
        if not parts:
            pass
        elif len(parts) == 1:
            url += f'?{url_single}={parts[0].pk}'
        elif len(parts) > 1:
            url += '?&'.join([f'{url_single}s={item.pk}' for item in parts])

        # Append an invalid item
        if invalid:
            url += f'&{url_single}{"s" if len(parts) > 1 else ""}=abc'

        # Append plugin reference
        if plugin_ref:
            url += f'&plugin={plugin_ref}'

        return url

    def test_wrong_implementation(self):
        """Test that a wrong implementation raises an error"""

        class WrongPlugin(LabelPrintingMixin, InvenTreePlugin):
            pass

        with self.assertRaises(MixinNotImplementedError):
            plugin = WrongPlugin()
            plugin.print_label('test')

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

        self.do_activate_plugin()
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

        url = self.do_url([part], plugin_ref, label)

        # Non-exsisting plugin
        response = self.get(f'{url}123', expected_code=404)
        self.assertIn(f'Plugin \'{plugin_ref}123\' not found', str(response.content, 'utf8'))

        # Inactive plugin
        response = self.get(url, expected_code=400)
        self.assertIn(f'Plugin \'{plugin_ref}\' is not enabled', str(response.content, 'utf8'))

        # Active plugin
        self.do_activate_plugin()

        # Print one part
        self.get(url, expected_code=200)

        # Print multiple parts
        self.get(self.do_url(Part.objects.all()[:2], plugin_ref, label), expected_code=200)

        # Print multiple parts without a plugin
        self.get(self.do_url(Part.objects.all()[:2], None, label), expected_code=200)

        # Print no part
        self.get(self.do_url(None, plugin_ref, label), expected_code=400)

    def test_printing_endpoints(self):
        """Cover the endpoints not covered by `test_printing_process`"""
        plugin_ref = 'samplelabel'

        # Activate the label components
        apps.get_app_config('label').create_labels()
        self.do_activate_plugin()

        def run_print_test(label, qs, url_name, url_single):
            """Run tests on single and multiple page printing

            Args:
                label (_type_): class of the label
                qs (_type_): class of the base queryset
                url_name (_type_): url for endpoints
                url_single (_type_): item lookup reference
            """
            label = label.objects.first()
            qs = qs.objects.all()

            # List endpoint
            self.get(self.do_url(None, None, None, f'{url_name}-list', url_single), expected_code=200)

            # List endpoint with filter
            self.get(self.do_url(qs[:2], None, None, f'{url_name}-list', url_single, invalid=True), expected_code=200)

            # Single page printing
            self.get(self.do_url(qs[:1], plugin_ref, label, f'{url_name}-print', url_single), expected_code=200)

            # Multi page printing
            self.get(self.do_url(qs[:2], plugin_ref, label, f'{url_name}-print', url_single), expected_code=200)

        # Test StockItemLabels
        run_print_test(StockItemLabel, StockItem, 'api-stockitem-label', 'item')

        # Test StockLocationLabels
        run_print_test(StockLocationLabel, StockLocation, 'api-stocklocation-label', 'location')

        # Test PartLabels
        run_print_test(PartLabel, Part, 'api-part-label', 'part')
