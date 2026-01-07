"""Unit tests for locate_sample sample plugins."""

from django.urls import reverse

from common.models import ParameterTemplate
from company.models import ManufacturerPart, SupplierPart
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part, PartCategory, PartCategoryParameterTemplate
from plugin import registry


class SampleSupplierTest(InvenTreeAPITestCase):
    """Tests for SampleSupplierPlugin."""

    fixtures = ['location', 'category', 'part', 'stock', 'company']
    roles = ['part.add']

    def test_list(self):
        """Check the list api."""
        # Test APIs
        url = reverse('api-supplier-list')

        # No plugin
        res = self.get(url, expected_code=200)
        self.assertEqual(len(res.data), 0)

        # Activate plugin
        config = registry.get_plugin('samplesupplier', active=None).plugin_config()
        config.active = True
        config.save()

        # One active plugin
        res = self.get(url, expected_code=200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['plugin_slug'], 'samplesupplier')
        self.assertEqual(res.data[0]['supplier_slug'], 'sample-fasteners')
        self.assertEqual(res.data[0]['supplier_name'], 'Sample Fasteners')

    def test_search(self):
        """Check the search api."""
        # Activate plugin
        config = registry.get_plugin('samplesupplier', active=None).plugin_config()
        config.active = True
        config.save()

        # Test APIs
        url = reverse('api-supplier-search')

        # No plugin
        self.get(
            url,
            {'plugin': 'non-existent-plugin', 'supplier': 'sample-fasteners'},
            expected_code=404,
        )

        # No supplier
        self.get(
            url,
            {'plugin': 'samplesupplier', 'supplier': 'non-existent-supplier'},
            expected_code=404,
        )

        # valid supplier
        res = self.get(
            url,
            {'plugin': 'samplesupplier', 'supplier': 'sample-fasteners', 'term': 'M5'},
            expected_code=200,
        )
        self.assertEqual(len(res.data), 15)
        self.assertEqual(res.data[0]['sku'], 'BOLT-Steel-M5-5')

    def test_import_part(self):
        """Test importing a part by supplier."""
        # Activate plugin
        plugin = registry.get_plugin('samplesupplier', active=None)
        config = plugin.plugin_config()
        config.active = True
        config.save()

        # Test APIs
        url = reverse('api-supplier-import')

        # No plugin
        self.post(
            url,
            {
                'plugin': 'non-existent-plugin',
                'supplier': 'sample-fasteners',
                'part_import_id': 'BOLT-Steel-M5-5',
            },
            expected_code=404,
        )

        # No supplier
        self.post(
            url,
            {
                'plugin': 'samplesupplier',
                'supplier': 'non-existent-supplier',
                'part_import_id': 'BOLT-Steel-M5-5',
            },
            expected_code=404,
        )

        # valid supplier, no part or category provided
        self.post(
            url,
            {
                'plugin': 'samplesupplier',
                'supplier': 'sample-fasteners',
                'part_import_id': 'BOLT-Steel-M5-5',
            },
            expected_code=400,
        )

        # valid supplier, but no supplier company set
        self.post(
            url,
            {
                'plugin': 'samplesupplier',
                'supplier': 'sample-fasteners',
                'part_import_id': 'BOLT-Steel-M5-5',
                'category_id': 1,
            },
            expected_code=500,
        )

        # Set the supplier company now
        plugin.set_setting('SUPPLIER', 1)

        # valid supplier, valid part import
        category = PartCategory.objects.get(pk=1)
        p_len = ParameterTemplate(name='Length', units='mm')
        p_test = ParameterTemplate(name='Test Parameter')
        p_len.save()
        p_test.save()
        PartCategoryParameterTemplate.objects.bulk_create([
            PartCategoryParameterTemplate(category=category, template=p_len),
            PartCategoryParameterTemplate(
                category=category, template=p_test, default_value='Test Value'
            ),
        ])
        res = self.post(
            url,
            {
                'plugin': 'samplesupplier',
                'supplier': 'sample-fasteners',
                'part_import_id': 'BOLT-Steel-M5-5',
                'category_id': 1,
            },
            expected_code=200,
        )
        part = Part.objects.get(name='BOLT-Steel-M5-5')
        self.assertIsNotNone(part)
        self.assertEqual(part.pk, res.data['part_id'])

        self.assertIsNotNone(SupplierPart.objects.get(pk=res.data['supplier_part_id']))
        self.assertIsNotNone(
            ManufacturerPart.objects.get(pk=res.data['manufacturer_part_id'])
        )

        self.assertSetEqual(
            {x['name'] for x in res.data['parameters']},
            {'Thread', 'Length', 'Material', 'Head', 'Test Parameter'},
        )
        for p in res.data['parameters']:
            if p['name'] == 'Length':
                self.assertEqual(p['value'], '5mm')
                self.assertEqual(p['parameter_template'], p_len.pk)
                self.assertTrue(p['on_category'])
            elif p['name'] == 'Test Parameter':
                self.assertEqual(p['value'], 'Test Value')
                self.assertEqual(p['parameter_template'], p_test.pk)
                self.assertTrue(p['on_category'])

        # valid supplier, import only manufacturer and supplier part
        part2 = Part.objects.create(name='Test Part', purchaseable=True)
        res = self.post(
            url,
            {
                'plugin': 'samplesupplier',
                'supplier': 'sample-fasteners',
                'part_import_id': 'BOLT-Steel-M5-10',
                'part_id': part2.pk,
            },
            expected_code=200,
        )

        self.assertEqual(part2.pk, res.data['part_id'])
        sp = SupplierPart.objects.get(pk=res.data['supplier_part_id'])
        mp = ManufacturerPart.objects.get(pk=res.data['manufacturer_part_id'])
        self.assertIsNotNone(sp)
        self.assertIsNotNone(mp)
        self.assertEqual(sp.part.pk, part2.pk)
        self.assertEqual(mp.part.pk, part2.pk)

        # PartNotFoundError
        self.post(
            url,
            {
                'plugin': 'samplesupplier',
                'supplier': 'sample-fasteners',
                'part_import_id': 'non-existent-part',
                'category_id': 1,
            },
            expected_code=404,
        )
