"""Tests barcode parsing for all suppliers."""

from django.urls import reverse

from company.models import Company, ManufacturerPart, SupplierPart
from order.models import PurchaseOrder, PurchaseOrderLineItem
from part.models import Part
from stock.models import StockItem, StockLocation

from InvenTree.unit_test import InvenTreeAPITestCase


class SupplierBarcodeTests(InvenTreeAPITestCase):
    """Tests barcode parsing for all suppliers."""

    SCAN_URL = reverse('api-barcode-scan')

    @classmethod
    def setUpTestData(cls):
        """Create supplier parts for barcodes."""
        super().setUpTestData()

        part = Part.objects.create(name='Test Part', description='Test Part')

        manufacturer = Company.objects.create(
            name='Test Manufacturer', is_manufacturer=True
        )

        mpart1 = ManufacturerPart.objects.create(
            part=part, manufacturer=manufacturer, MPN='MC34063ADR'
        )
        mpart2 = ManufacturerPart.objects.create(
            part=part, manufacturer=manufacturer, MPN='LDK320ADU33R'
        )

        supplier = Company.objects.create(name='Supplier', is_supplier=True)
        mouser = Company.objects.create(name='Mouser Test', is_supplier=True)

        supplier_parts = [
            SupplierPart(SKU='296-LM358BIDDFRCT-ND', part=part, supplier=supplier),
            SupplierPart(SKU='1', part=part, manufacturer_part=mpart1, supplier=mouser),
            SupplierPart(SKU='2', part=part, manufacturer_part=mpart2, supplier=mouser),
            SupplierPart(SKU='C312270', part=part, supplier=supplier),
            SupplierPart(SKU='WBP-302', part=part, supplier=supplier),
        ]

        SupplierPart.objects.bulk_create(supplier_parts)

    def test_digikey_barcode(self):
        """Test digikey barcode."""
        result = self.post(
            self.SCAN_URL, data={'barcode': DIGIKEY_BARCODE}, expected_code=200
        )
        self.assertEqual(result.data['plugin'], 'DigiKeyPlugin')

        supplier_part_data = result.data.get('supplierpart')
        self.assertIn('pk', supplier_part_data)

        supplier_part = SupplierPart.objects.get(pk=supplier_part_data['pk'])
        self.assertEqual(supplier_part.SKU, '296-LM358BIDDFRCT-ND')

    def test_digikey_2_barcode(self):
        """Test digikey barcode which uses 30P instead of P."""
        result = self.post(
            self.SCAN_URL, data={'barcode': DIGIKEY_BARCODE_2}, expected_code=200
        )
        self.assertEqual(result.data['plugin'], 'DigiKeyPlugin')

        supplier_part_data = result.data.get('supplierpart')
        self.assertIn('pk', supplier_part_data)

        supplier_part = SupplierPart.objects.get(pk=supplier_part_data['pk'])
        self.assertEqual(supplier_part.SKU, '296-LM358BIDDFRCT-ND')

    def test_digikey_3_barcode(self):
        """Test digikey barcode which is invalid."""
        self.post(self.SCAN_URL, data={'barcode': DIGIKEY_BARCODE_3}, expected_code=400)

    def test_mouser_barcode(self):
        """Test mouser barcode with custom order number."""
        result = self.post(
            self.SCAN_URL, data={'barcode': MOUSER_BARCODE}, expected_code=200
        )

        supplier_part_data = result.data.get('supplierpart')
        self.assertIn('pk', supplier_part_data)

        supplier_part = SupplierPart.objects.get(pk=supplier_part_data['pk'])
        self.assertEqual(supplier_part.SKU, '1')

    def test_old_mouser_barcode(self):
        """Test old mouser barcode with messed up header."""
        result = self.post(
            self.SCAN_URL, data={'barcode': MOUSER_BARCODE_OLD}, expected_code=200
        )

        supplier_part_data = result.data.get('supplierpart')
        self.assertIn('pk', supplier_part_data)
        supplier_part = SupplierPart.objects.get(pk=supplier_part_data['pk'])
        self.assertEqual(supplier_part.SKU, '2')

    def test_lcsc_barcode(self):
        """Test LCSC barcode."""
        result = self.post(
            self.SCAN_URL, data={'barcode': LCSC_BARCODE}, expected_code=200
        )

        self.assertEqual(result.data['plugin'], 'LCSCPlugin')

        supplier_part_data = result.data.get('supplierpart')
        self.assertIn('pk', supplier_part_data)

        supplier_part = SupplierPart.objects.get(pk=supplier_part_data['pk'])
        self.assertEqual(supplier_part.SKU, 'C312270')

    def test_tme_qrcode(self):
        """Test TME QR-Code."""
        result = self.post(
            self.SCAN_URL, data={'barcode': TME_QRCODE}, expected_code=200
        )

        self.assertEqual(result.data['plugin'], 'TMEPlugin')

        supplier_part_data = result.data.get('supplierpart')
        self.assertIn('pk', supplier_part_data)
        supplier_part = SupplierPart.objects.get(pk=supplier_part_data['pk'])
        self.assertEqual(supplier_part.SKU, 'WBP-302')

    def test_tme_barcode2d(self):
        """Test TME DataMatrix-Code."""
        result = self.post(
            self.SCAN_URL, data={'barcode': TME_DATAMATRIX_CODE}, expected_code=200
        )

        self.assertEqual(result.data['plugin'], 'TMEPlugin')

        supplier_part_data = result.data.get('supplierpart')
        self.assertIn('pk', supplier_part_data)

        supplier_part = SupplierPart.objects.get(pk=supplier_part_data['pk'])
        self.assertEqual(supplier_part.SKU, 'WBP-302')


class SupplierBarcodePOReceiveTests(InvenTreeAPITestCase):
    """Tests barcode scanning to receive a purchase order item."""

    def setUp(self):
        """Create supplier part and purchase_order."""
        super().setUp()

        part = Part.objects.create(name='Test Part', description='Test Part')
        supplier = Company.objects.create(name='Supplier', is_supplier=True)
        manufacturer = Company.objects.create(
            name='Test Manufacturer', is_manufacturer=True
        )

        mouser = Company.objects.create(name='Mouser Test', is_supplier=True)
        mpart = ManufacturerPart.objects.create(
            part=part, manufacturer=manufacturer, MPN='MC34063ADR'
        )

        self.purchase_order1 = PurchaseOrder.objects.create(
            supplier_reference='72991337', supplier=supplier
        )

        supplier_parts1 = [
            SupplierPart(SKU=f'1_{i}', part=part, supplier=supplier) for i in range(6)
        ]

        supplier_parts1.insert(
            2, SupplierPart(SKU='296-LM358BIDDFRCT-ND', part=part, supplier=supplier)
        )

        for supplier_part in supplier_parts1:
            supplier_part.save()
            self.purchase_order1.add_line_item(supplier_part, 8)

        self.purchase_order2 = PurchaseOrder.objects.create(
            reference='P0-1337', supplier=mouser
        )

        self.purchase_order2.place_order()
        supplier_parts2 = [
            SupplierPart(SKU=f'2_{i}', part=part, supplier=mouser) for i in range(6)
        ]

        supplier_parts2.insert(
            3,
            SupplierPart(SKU='42', part=part, manufacturer_part=mpart, supplier=mouser),
        )

        for supplier_part in supplier_parts2:
            supplier_part.save()
            self.purchase_order2.add_line_item(supplier_part, 5)

    def test_receive(self):
        """Test receiving an item from a barcode."""
        url = reverse('api-barcode-po-receive')

        result1 = self.post(url, data={'barcode': DIGIKEY_BARCODE}, expected_code=400)

        assert result1.data['error'].startswith('No matching purchase order')

        self.purchase_order1.place_order()

        result2 = self.post(url, data={'barcode': DIGIKEY_BARCODE}, expected_code=200)
        self.assertIn('success', result2.data)

        result3 = self.post(url, data={'barcode': DIGIKEY_BARCODE}, expected_code=400)
        self.assertEqual(result3.data['error'], 'Item has already been received')

        result4 = self.post(
            url, data={'barcode': DIGIKEY_BARCODE[:-1]}, expected_code=400
        )
        assert result4.data['error'].startswith(
            'Failed to find pending line item for supplier part'
        )

        result5 = self.post(
            reverse('api-barcode-scan'),
            data={'barcode': DIGIKEY_BARCODE},
            expected_code=200,
        )
        stock_item = StockItem.objects.get(pk=result5.data['stockitem']['pk'])
        assert stock_item.supplier_part.SKU == '296-LM358BIDDFRCT-ND'
        assert stock_item.quantity == 10
        assert stock_item.location is None

    def test_receive_custom_order_number(self):
        """Test receiving an item from a barcode with a custom order number."""
        url = reverse('api-barcode-po-receive')
        result1 = self.post(url, data={'barcode': MOUSER_BARCODE})
        assert 'success' in result1.data

        result2 = self.post(
            reverse('api-barcode-scan'), data={'barcode': MOUSER_BARCODE}
        )
        stock_item = StockItem.objects.get(pk=result2.data['stockitem']['pk'])
        assert stock_item.supplier_part.SKU == '42'
        assert stock_item.supplier_part.manufacturer_part.MPN == 'MC34063ADR'
        assert stock_item.quantity == 3
        assert stock_item.location is None

    def test_receive_one_stock_location(self):
        """Test receiving an item when only one stock location exists."""
        stock_location = StockLocation.objects.create(name='Test Location')

        url = reverse('api-barcode-po-receive')
        result1 = self.post(url, data={'barcode': MOUSER_BARCODE})
        assert 'success' in result1.data

        result2 = self.post(
            reverse('api-barcode-scan'), data={'barcode': MOUSER_BARCODE}
        )
        stock_item = StockItem.objects.get(pk=result2.data['stockitem']['pk'])
        assert stock_item.location == stock_location

    def test_receive_default_line_item_location(self):
        """Test receiving an item into the default line_item location."""
        StockLocation.objects.create(name='Test Location 1')
        stock_location2 = StockLocation.objects.create(name='Test Location 2')

        line_item = PurchaseOrderLineItem.objects.filter(part__SKU='42')[0]
        line_item.destination = stock_location2
        line_item.save()

        url = reverse('api-barcode-po-receive')
        result1 = self.post(url, data={'barcode': MOUSER_BARCODE})
        assert 'success' in result1.data

        result2 = self.post(
            reverse('api-barcode-scan'), data={'barcode': MOUSER_BARCODE}
        )
        stock_item = StockItem.objects.get(pk=result2.data['stockitem']['pk'])
        assert stock_item.location == stock_location2

    def test_receive_default_part_location(self):
        """Test receiving an item into the default part location."""
        StockLocation.objects.create(name='Test Location 1')
        stock_location2 = StockLocation.objects.create(name='Test Location 2')

        part = Part.objects.all()[0]
        part.default_location = stock_location2
        part.save()

        url = reverse('api-barcode-po-receive')
        result1 = self.post(url, data={'barcode': MOUSER_BARCODE})
        assert 'success' in result1.data

        result2 = self.post(
            reverse('api-barcode-scan'), data={'barcode': MOUSER_BARCODE}
        )
        stock_item = StockItem.objects.get(pk=result2.data['stockitem']['pk'])
        assert stock_item.location == stock_location2

    def test_receive_specific_order_and_location(self):
        """Test receiving an item from a specific order into a specific location."""
        StockLocation.objects.create(name='Test Location 1')
        stock_location2 = StockLocation.objects.create(name='Test Location 2')

        url = reverse('api-barcode-po-receive')
        barcode = MOUSER_BARCODE.replace('\x1dKP0-1337', '')
        result1 = self.post(
            url,
            data={
                'barcode': barcode,
                'purchase_order': self.purchase_order2.pk,
                'location': stock_location2.pk,
            },
        )
        assert 'success' in result1.data

        result2 = self.post(reverse('api-barcode-scan'), data={'barcode': barcode})
        stock_item = StockItem.objects.get(pk=result2.data['stockitem']['pk'])
        assert stock_item.location == stock_location2

    def test_receive_missing_quantity(self):
        """Test receiving an with missing quantity information."""
        url = reverse('api-barcode-po-receive')
        barcode = MOUSER_BARCODE.replace('\x1dQ3', '')
        response = self.post(url, data={'barcode': barcode}, expected_code=200)

        assert 'lineitem' in response.data
        assert 'quantity' not in response.data['lineitem']


DIGIKEY_BARCODE = (
    '[)>\x1e06\x1dP296-LM358BIDDFRCT-ND\x1d1PLM358BIDDFR\x1dK\x1d1K72991337\x1d'
    '10K85781337\x1d11K1\x1d4LPH\x1dQ10\x1d11ZPICK\x1d12Z15221337\x1d13Z361337'
    '\x1d20Z0000000000000000000000000000000000000000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000'
    '0000000000000000000000000000000000'
)

# Uses 30P instead of P
DIGIKEY_BARCODE_2 = (
    '[)>\x1e06\x1d30P296-LM358BIDDFRCT-ND\x1dK\x1d1K72991337\x1d'
    '10K85781337\x1d11K1\x1d4LPH\x1dQ10\x1d11ZPICK\x1d12Z15221337\x1d13Z361337'
    '\x1d20Z0000000000000000000000000000000000000000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000'
    '0000000000000000000000000000000000'
)

# Invalid code
DIGIKEY_BARCODE_3 = (
    '[)>\x1e06\x1dPnonsense\x1d30Pnonsense\x1d1Pnonsense\x1dK\x1d1K72991337\x1d'
    '10K85781337\x1d11K1\x1d4LPH\x1dQ10\x1d11ZPICK\x1d12Z15221337\x1d13Z361337'
    '\x1d20Z0000000000000000000000000000000000000000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000'
    '0000000000000000000000000000000000'
)

MOUSER_BARCODE = (
    '[)>\x1e06\x1dKP0-1337\x1d14K011\x1d1PMC34063ADR\x1dQ3\x1d11K073121337\x1d4'
    'LMX\x1d1VTI\x1e\x04'
)

MOUSER_BARCODE_OLD = (
    '>[)>06\x1dK21421337\x1d14K033\x1d1PLDK320ADU33R\x1dQ32\x1d11K060931337\x1d'
    '4LCN\x1d1VSTMicro'
)

LCSC_BARCODE = (
    '{pbn:PICK2009291337,on:SO2009291337,pc:C312270,pm:ST-1-102-A01-T000-RS,qty'
    ':2,mc:,cc:1,pdi:34421807}'
)

TME_QRCODE = (
    'QTY:1 PN:WBP-302 PO:19361337/1 CPO:PO-2023-06-08-001337 MFR:WISHERENTERPRI'
    'SE MPN:WBP-302 RoHS https://www.tme.eu/details/WBP-302'
)

TME_DATAMATRIX_CODE = 'PWBP-302 1PMPNWBP-302 Q1 K19361337/1'
