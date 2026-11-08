"""Unit test for the exporter plugins."""

from django.test import TestCase
from django.urls import reverse

from InvenTree.helpers import escape_export_value
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
                excluded_cols=['External Stock', 'Variant Stock'],
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


class FormulaInjectionExportTest(InvenTreeAPITestCase):
    """Test that exported data is escaped to prevent formula injection.

    Ref: https://owasp.org/www-community/attacks/CSV_Injection
    """

    roles = ['part.view']

    NAMES = {
        '=2+2': "'=2+2",
        '+1+1': "'+1+1",
        '-12V Regulator': "'-12V Regulator",
        '@SUM(1)': "'@SUM(1)",
        'Safe Part': 'Safe Part',
    }

    @classmethod
    def setUpTestData(cls):
        """Create parts with names which could be interpreted as formulae."""
        from part.models import Part, PartCategory

        super().setUpTestData()

        cls.category = PartCategory.objects.create(name='Formula Category')

        for name in cls.NAMES:
            Part.objects.create(
                name=name, description='Formula test', category=cls.category
            )

    def test_csv_export(self):
        """Malicious string values are prefixed when exported to CSV."""
        url = reverse('api-part-list')

        with self.export_data(
            url, params={'category': self.category.pk}, export_format='csv'
        ) as data_file:
            data = self.process_csv(
                data_file, required_cols=['Name'], required_rows=len(self.NAMES)
            )

        names = {row['Name'] for row in data}
        self.assertEqual(names, set(self.NAMES.values()))

    def test_xlsx_export(self):
        """Malicious string values are not written as formula cells in XLSX."""
        import openpyxl

        url = reverse('api-part-list')

        with self.export_data(
            url,
            params={'category': self.category.pk},
            export_format='xlsx',
            decode=False,
        ) as data_file:
            workbook = openpyxl.load_workbook(data_file)

        sheet = workbook.active
        headers = [cell.value for cell in sheet[1]]
        col = headers.index('Name') + 1

        names = set()

        for row in sheet.iter_rows(min_row=2, min_col=col, max_col=col):
            cell = row[0]
            self.assertNotEqual(cell.data_type, 'f')
            names.add(cell.value)

        self.assertEqual(names, set(self.NAMES.values()))


class EscapeExportValueTest(TestCase):
    """Unit tests for the escape_export_value helper."""

    def test_numeric_unchanged(self):
        """Strictly numeric values are not escaped, even with a +/- prefix."""
        for value in ['123', '-222', '+5', '123.4', '-123.4', '+.5', '12e6', '-1.5E-3']:
            self.assertEqual(escape_export_value(value), value)

    def test_non_numeric_escaped(self):
        """Non-numeric values with a dangerous prefix are escaped."""
        for value in [
            '=2+2',
            '+1+1',
            '-1-1',
            '-12V Regulator',
            '-',
            '+',
            '-1e',
            '-nan',
            '-inf',
            '-1 ',
            '- 1',
            '-1,2',
            '@SUM(1)',
            '\tabc',
            '\rabc',
        ]:
            self.assertEqual(escape_export_value(value), "'" + value)

    def test_other_values(self):
        """Safe strings and non-string values are returned unchanged."""
        for value in ['Safe Part', '', 'a-b', 42, -42, 1.5, None, True]:
            self.assertEqual(escape_export_value(value), value)
