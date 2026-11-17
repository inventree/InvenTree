"""Unit tests for the ManufacturerBarcodePlugin."""

from django.contrib.auth import get_user_model
from django.urls import reverse

from company.models import Company, ManufacturerPart, SupplierPart
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from plugin import PluginMixinEnum, registry
from plugin.builtin.barcodes.manufacturer_barcode import ManufacturerBarcodePlugin

PLUGIN_NAME = 'ManufacturerBarcodePlugin'
PLUGIN_SLUG = 'manufacturerbarcode'


def ecia(*fields: str) -> str:
    """Construct an ECIA / ISO 15434 barcode from the provided fields."""
    return '[)>\x1e06\x1d' + '\x1d'.join(fields) + '\x1e\x04'


class ManufacturerBarcodeParseTests(InvenTreeAPITestCase):
    """Tests for extracting MPN candidates from barcode data (no database lookups)."""

    def test_datamatrix(self):
        """Test extraction from GS / RS delimited barcodes."""
        extract = ManufacturerBarcodePlugin.extract_mpn_candidates

        # 1P field
        self.assertEqual(extract(ecia('K123', '1PLM358', 'Q10')), ['LM358'])

        # P field only
        self.assertEqual(extract(ecia('K123', 'PLM358', 'Q10')), ['LM358'])

        # 1P is preferred over P, regardless of field order
        self.assertEqual(extract(ecia('PSKU-123', '1PLM358')), ['LM358'])

        # 30P (supplier part number) and 11P are not MPN fields
        self.assertEqual(extract(ecia('30PSKU-123', '11PXYZ')), [])

        # No header, GS separators only
        self.assertEqual(extract('K123\x1d1PLM358\x1dQ10'), ['LM358'])

        # Old style Mouser header
        self.assertEqual(extract('>[)>06\x1dK1\x1d1PLM358\x1dQ3'), ['LM358'])

        # Raw data is never used as a candidate for structured barcodes
        self.assertEqual(extract(ecia('K123', 'Q10')), [])

        # Empty MPN field
        self.assertEqual(extract(ecia('1P', 'Q10')), [])

    def test_simple(self):
        """Test extraction from simple (single field) barcodes."""
        extract = ManufacturerBarcodePlugin.extract_mpn_candidates

        self.assertEqual(extract('1PLM358'), ['LM358', '1PLM358'])
        self.assertEqual(extract('PLM358'), ['LM358', 'PLM358'])
        self.assertEqual(extract('  LM358 \n'), ['LM358'])
        self.assertEqual(extract('LM358'), ['LM358'])

        # Invalid data
        self.assertEqual(extract(''), [])
        self.assertEqual(extract('   '), [])
        self.assertEqual(extract(None), [])
        self.assertEqual(extract(123), [])
        self.assertEqual(extract('LM\x00358'), [])

        # Exceeds the maximum MPN length
        self.assertEqual(extract('X' * 1000), [])


class ManufacturerBarcodeTests(InvenTreeAPITestCase):
    """Tests for scanning manufacturer part barcodes via the API."""

    SCAN_URL = reverse('api-barcode-scan')

    roles = ['part.view', 'purchase_order.view', 'stock.view']

    @classmethod
    def setUpTestData(cls):
        """Create manufacturer parts to match against."""
        super().setUpTestData()

        # Only the DigiKey supplier plugin is active for these tests
        registry.set_plugin_states({
            PLUGIN_SLUG: True,
            'digikeyplugin': True,
            'mouserplugin': False,
            'lcscplugin': False,
            'tmeplugin': False,
        })

        # Note: The DigiKey plugin must have a supplier configured,
        # otherwise it will match *any* ECIA barcode by MPN alone
        cls.digikey = Company.objects.create(name='DigiKey', is_supplier=True)
        registry.get_plugin('digikeyplugin').set_setting('SUPPLIER_ID', cls.digikey.pk)

        cls.part = Part.objects.create(name='Test Part', description='Test Part')

        cls.manufacturer_a = Company.objects.create(
            name='Manufacturer A', is_manufacturer=True
        )
        cls.manufacturer_b = Company.objects.create(
            name='Manufacturer B', is_manufacturer=True
        )

        def create(manufacturer, mpn):
            return ManufacturerPart.objects.create(
                part=cls.part, manufacturer=manufacturer, MPN=mpn
            )

        # Unique MPN values
        cls.lm358 = create(cls.manufacturer_a, 'LM358')
        cls.pic = create(cls.manufacturer_a, 'PIC16F84A')

        # Same MPN from two different manufacturers
        create(cls.manufacturer_a, 'NE555')
        create(cls.manufacturer_b, 'NE555')

        # 'PX1' could be either 'P' + 'X1' or the raw MPN 'PX1'
        create(cls.manufacturer_a, 'X1')
        create(cls.manufacturer_a, 'PX1')

    def setUp(self):
        """Clear any supplier cached by the DigiKey plugin in a previous test."""
        super().setUp()
        registry.get_plugin('digikeyplugin').__dict__.pop('_supplier', None)

    def scan(self, barcode: str, expected_code: int = 200):
        """Scan the provided barcode."""
        return self.post(
            self.SCAN_URL, data={'barcode': barcode}, expected_code=expected_code
        ).data

    def assertMatch(self, barcode: str, manufacturer_part: ManufacturerPart):
        """Assert that the barcode matches the provided ManufacturerPart."""
        data = self.scan(barcode)
        self.assertEqual(data['plugin'], PLUGIN_NAME)
        self.assertEqual(data['manufacturerpart']['pk'], manufacturer_part.pk)

    def assertNoMatch(self, barcode: str):
        """Assert that the barcode does not match."""
        data = self.scan(barcode, expected_code=400)
        self.assertIn('error', data)
        self.assertNotIn('manufacturerpart', data)

    def test_plugin_priority(self):
        """The manufacturer barcode plugin has a lower priority than all other barcode plugins.

        Note: The actual query order is tested in plugin.base.barcodes.test_barcode,
        and via the API in test_internal_barcode / test_supplier_plugin_preferred.
        """
        plugin = registry.get_plugin(PLUGIN_SLUG)
        others = [
            plg
            for plg in registry.with_mixin(PluginMixinEnum.BARCODE)
            if plg.slug != PLUGIN_SLUG
        ]

        self.assertLess(plugin.BARCODE_PRIORITY, 0)
        self.assertGreater(len(others), 0)

        for other in others:
            self.assertGreater(other.BARCODE_PRIORITY, plugin.BARCODE_PRIORITY)

    def test_datamatrix(self):
        """Test scanning of structured barcodes."""
        self.assertMatch(ecia('K123', '1PLM358', 'Q10'), self.lm358)
        self.assertMatch(ecia('K123', 'PLM358', 'Q10'), self.lm358)

        # 1P takes precedence - an unmatched 1P does not fall back to P
        self.assertNoMatch(ecia('PLM358', '1PUNKNOWN'))

        # No MPN fields
        self.assertNoMatch(ecia('K123', 'Q10'))

    def test_simple(self):
        """Test scanning of simple prefixed barcodes and raw MPN values."""
        for barcode in ['1PLM358', 'PLM358', 'LM358', ' LM358 ']:
            self.assertMatch(barcode, self.lm358)

        # Raw MPN which happens to start with 'P'
        self.assertMatch('PIC16F84A', self.pic)

    def test_exact_match(self):
        """Partial matches are not accepted."""
        for barcode in ['LM35', 'LM3588', 'XLM358', ecia('1PLM35')]:
            self.assertNoMatch(barcode)

    def test_ambiguous(self):
        """Multiple matching ManufacturerPart instances must not return a match."""
        self.assertNoMatch('NE555')
        self.assertNoMatch('1PNE555')
        self.assertNoMatch(ecia('1PNE555'))

        # 'PX1' matches both 'X1' (prefix stripped) and 'PX1' (raw)
        self.assertNoMatch('PX1')

    def test_internal_barcode(self):
        """An internal barcode is matched by the internal plugin, not this plugin."""
        self.lm358.part.assign_barcode(barcode_data='LM358')

        data = self.scan('LM358')
        self.assertEqual(data['plugin'], 'InvenTreeBarcode')
        self.assertEqual(data['part']['pk'], self.part.pk)

    def test_supplier_plugin_preferred(self):
        """A supplier barcode plugin match takes precedence over this plugin."""
        supplier = self.digikey

        barcode = ecia('PDK-LM358-ND', '1PLM358', 'Q10')

        # No supplier part - falls back to the manufacturer part
        self.assertMatch(barcode, self.lm358)

        supplier_part = SupplierPart.objects.create(
            part=self.part,
            supplier=supplier,
            SKU='DK-LM358-ND',
            manufacturer_part=self.lm358,
        )

        data = self.scan(barcode)
        self.assertEqual(data['plugin'], 'DigiKeyBarcodePlugin')
        self.assertEqual(data['supplierpart']['pk'], supplier_part.pk)

    def test_permission(self):
        """Users without permission to view manufacturer parts get no match."""
        user = get_user_model().objects.create_user(
            username='no-perms', password='no-perms-password'
        )

        plugin = registry.get_plugin(PLUGIN_SLUG)
        self.assertIsNone(plugin.scan('LM358', user=user))
        self.assertIsNone(plugin.scan('LM358', user=None))

        # Sanity check - the API user can see the match
        self.assertIsNotNone(plugin.scan('LM358', user=self.user))
