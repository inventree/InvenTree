"""Unit test for the exporter plugins."""

from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase
from plugin.registry import registry


class StocktakeExporterTest(InvenTreeAPITestCase):
    """Test the stocktake exporter plugin."""

    fixtures = ['category', 'part', 'location', 'stock', 'bom', 'company']
    roles = ['part.add', 'part.change', 'part.delete', 'stock.view']

    def test_stocktake_exporter(self):
        """Test the stocktake exporter plugin."""
        from part.models import Part

        slug = 'inventree-stocktake-exporter'

        registry.set_plugin_state(slug, True)

        url = reverse('api-part-list')

        # Download all part data using the 'stocktake' exporter
        # Use the "default" values
        with self.export_data(
            url, export_plugin=slug, export_format='csv'
        ) as data_file:
            self.process_csv(
                data_file,
                required_rows=Part.objects.count(),
                required_cols=[
                    'Name',
                    'IPN',
                    'Total Stock',
                    'Minimum Unit Cost',
                    'Maximum Total Cost',
                ],
                excluded_cols=['Active', 'External Stock', 'Variant Stock'],
            )

        # Now, with additional parameters specific to the plugin
        with self.export_data(
            url,
            export_plugin=slug,
            export_format='csv',
            export_pricing_data=True,
            export_include_external_items=True,
            export_include_variant_items=True,
        ) as data_file:
            self.process_csv(
                data_file,
                required_rows=Part.objects.count(),
                required_cols=[
                    'Total Stock',
                    'On Order',
                    'Minimum Unit Cost',
                    'Maximum Total Cost',
                    'External Stock',
                    'Variant Stock',
                ],
                excluded_cols=['Active'],
            )

        # Finally, exclude pricing data entirely
        with self.export_data(
            url, export_plugin=slug, export_format='csv', export_pricing_data=False
        ) as data_file:
            self.process_csv(
                data_file,
                required_rows=Part.objects.count(),
                required_cols=['Total Stock', 'On Order'],
                excluded_cols=[
                    'Minimum Unit Cost',
                    'Maximum Total Cost',
                    'Variant Stock',
                    'External Stock',
                ],
            )

        # Reset plugin state
        registry.set_plugin_state(slug, False)
