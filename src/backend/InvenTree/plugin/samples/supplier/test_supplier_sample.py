"""Unit tests for locate_sample sample plugins."""

from django.urls import reverse

from company.models import ManufacturerPart, SupplierPart
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from plugin import registry


class SampleSupplierTest(InvenTreeAPITestCase):
    """Tests for SampleSupplierPlugin."""

    fixtures = ['location', 'category', 'part', 'stock', 'company']
    roles = ['part.add']

    def test_search(self):
        """Check if the event is issued."""
        # Activate plugin
        config = registry.get_plugin('samplesupplier').plugin_config()
        config.active = True
        config.save()

        # Test APIs
        url = reverse('api-supplier-search')

        # No supplier
        self.get(url, {'supplier': 'non-existent-supplier'}, expected_code=404)

        # valid supplier
        res = self.get(
            url, {'supplier': 'samplesupplier', 'term': 'M5'}, expected_code=200
        )
        self.assertEqual(len(res.data), 15)
        self.assertEqual(res.data[0]['sku'], 'BOLT-Steel-M5-5')

    def test_import_part(self):
        """Test importing a part by supplier."""
        # Activate plugin
        plugin = registry.get_plugin('samplesupplier')
        config = plugin.plugin_config()
        config.active = True
        config.save()
        plugin.set_setting('SUPPLIER', 1)

        # Test APIs
        url = reverse('api-supplier-import')

        # No supplier
        self.post(url, {'supplier': 'non-existent-supplier'}, expected_code=400)

        # valid supplier, no part or category provided
        self.post(url, {'supplier': 'samplesupplier'}, expected_code=400)

        # valid supplier, valid part import
        res = self.post(
            url,
            {
                'supplier': 'samplesupplier',
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

        # valid supplier, import only manufacturer and supplier part
        part2 = Part.objects.create(name='Test Part', purchaseable=True)
        res = self.post(
            url,
            {
                'supplier': 'samplesupplier',
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
                'supplier': 'samplesupplier',
                'part_import_id': 'non-existent-part',
                'category_id': 1,
            },
            expected_code=404,
        )
