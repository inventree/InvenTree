"""Unit tests for Part pricing calculations."""

from django.core.exceptions import ObjectDoesNotExist
from django.test.utils import override_settings

from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money

import common.currency
import common.models
import common.settings
import company.models
import order.models
import part.models
import stock.models
from common.settings import set_global_setting
from InvenTree.unit_test import InvenTreeTestCase
from order.status_codes import PurchaseOrderStatus


class PartPricingTests(InvenTreeTestCase):
    """Unit tests for part pricing calculations."""

    def setUp(self):
        """Setup routines."""
        super().setUp()

        self.generate_exchange_rates()

        # Create a new part for performing pricing calculations
        # We will use 'metres' for the UOM here
        # Some SupplierPart instances will have different units!
        self.part = part.models.Part.objects.create(
            name='PP',
            description='A part with pricing, measured in metres',
            assembly=True,
            units='m',
        )

    def create_price_breaks(self):
        """Create some price breaks for the part, in various currencies."""
        # First supplier part (CAD)
        self.supplier_1 = company.models.Company.objects.create(
            name='Supplier 1', is_supplier=True
        )

        self.sp_1 = company.models.SupplierPart.objects.create(
            supplier=self.supplier_1,
            part=self.part,
            SKU='SUP_1',
            pack_quantity='200 cm',
        )

        # Native pack quantity should be 2m
        self.assertEqual(self.sp_1.pack_quantity_native, 2)

        company.models.SupplierPriceBreak.objects.create(
            part=self.sp_1, quantity=1, price=10.4, price_currency='CAD'
        )

        # Second supplier part (AUD)
        self.supplier_2 = company.models.Company.objects.create(
            name='Supplier 2', is_supplier=True
        )

        self.sp_2 = company.models.SupplierPart.objects.create(
            supplier=self.supplier_2, part=self.part, SKU='SUP_2', pack_quantity='2.5'
        )

        # Native pack quantity should be 2.5m
        self.assertEqual(self.sp_2.pack_quantity_native, 2.5)

        self.sp_3 = company.models.SupplierPart.objects.create(
            supplier=self.supplier_2,
            part=self.part,
            SKU='SUP_3',
            pack_quantity='10 inches',
        )

        # Native pack quantity should be 0.254m
        self.assertEqual(self.sp_3.pack_quantity_native, 0.254)

        company.models.SupplierPriceBreak.objects.create(
            part=self.sp_2, quantity=5, price=7.555, price_currency='AUD'
        )

        # Third supplier part (GBP)
        company.models.SupplierPriceBreak.objects.create(
            part=self.sp_2, quantity=10, price=4.55, price_currency='GBP'
        )

    @override_settings(TESTING_PRICING=True)
    def test_pricing_data(self):
        """Test link between Part and PartPricing model."""
        # Initially there is no associated Pricing data
        with self.assertRaises(ObjectDoesNotExist):
            pricing = self.part.pricing_data

        # Accessing in this manner should create the associated PartPricing instance
        pricing = self.part.pricing

        self.assertEqual(pricing.part, self.part)

        # Default values should be null
        self.assertIsNone(pricing.bom_cost_min)
        self.assertIsNone(pricing.bom_cost_max)

        self.assertIsNone(pricing.internal_cost_min)
        self.assertIsNone(pricing.internal_cost_max)

        self.assertIsNone(pricing.overall_min)
        self.assertIsNone(pricing.overall_max)

    def test_invalid_rate(self):
        """Ensure that conversion behaves properly with missing rates."""

    @override_settings(TESTING_PRICING=True)
    def test_simple(self):
        """Tests for hard-coded values."""
        pricing = self.part.pricing

        # Add internal pricing
        pricing.internal_cost_min = Money(1, 'USD')
        pricing.internal_cost_max = Money(4, 'USD')
        pricing.save()

        self.assertEqual(pricing.overall_min, Money('1', 'USD'))
        self.assertEqual(pricing.overall_max, Money('4', 'USD'))

        # Add supplier pricing
        pricing.supplier_price_min = Money(10, 'AUD')
        pricing.supplier_price_max = Money(15, 'CAD')
        pricing.save()

        # Minimum pricing should not have changed
        self.assertEqual(pricing.overall_min, Money('1', 'USD'))

        # Maximum price has changed, and was specified in a different currency
        self.assertEqual(pricing.overall_max, Money('8.823529', 'USD'))

        # Add BOM cost
        pricing.bom_cost_min = Money(0.1, 'GBP')
        pricing.bom_cost_max = Money(25, 'USD')
        pricing.save()

        self.assertEqual(pricing.overall_min, Money('0.111111', 'USD'))
        self.assertEqual(pricing.overall_max, Money('25', 'USD'))

    @override_settings(TESTING_PRICING=True)
    def test_supplier_part_pricing(self):
        """Test for supplier part pricing."""
        pricing = self.part.pricing

        # Initially, no information (not yet calculated)
        self.assertIsNone(pricing.supplier_price_min)
        self.assertIsNone(pricing.supplier_price_max)
        self.assertIsNone(pricing.overall_min)
        self.assertIsNone(pricing.overall_max)

        # Creating price breaks will cause the pricing to be updated
        self.create_price_breaks()

        pricing = self.part.pricing
        pricing.refresh_from_db()

        self.assertAlmostEqual(float(pricing.overall_min.amount), 2.015, places=2)
        self.assertAlmostEqual(float(pricing.overall_max.amount), 3.06, places=2)

        # Delete all supplier parts and re-calculate
        self.part.supplier_parts.all().delete()

        pricing = self.part.pricing
        pricing.refresh_from_db()

        self.assertIsNone(pricing.supplier_price_min)
        self.assertIsNone(pricing.supplier_price_max)

    @override_settings(TESTING_PRICING=True)
    def test_internal_pricing(self):
        """Tests for internal price breaks."""
        # Ensure internal pricing is enabled
        set_global_setting('PART_INTERNAL_PRICE', True, None)

        pricing = self.part.pricing

        # Initially, no internal price breaks
        self.assertIsNone(pricing.internal_cost_min)
        self.assertIsNone(pricing.internal_cost_max)

        currency = common.currency.currency_code_default()

        for ii in range(5):
            # Let's add some internal price breaks
            part.models.PartInternalPriceBreak.objects.create(
                part=self.part, quantity=ii + 1, price=10 - ii, price_currency=currency
            )

            pricing = self.part.pricing
            pricing.refresh_from_db()

            # Expected money value
            m_expected = Money(10 - ii, currency)

            # Minimum cost should keep decreasing as we add more items
            self.assertEqual(pricing.internal_cost_min, m_expected)
            self.assertEqual(pricing.overall_min, m_expected)

            # Maximum cost should stay the same
            self.assertEqual(pricing.internal_cost_max, Money(10, currency))
            self.assertEqual(pricing.overall_max, Money(10, currency))

    @override_settings(TESTING_PRICING=True)
    def test_stock_item_pricing(self):
        """Test for stock item pricing data."""
        # Create a part
        p = part.models.Part.objects.create(
            name='Test part for pricing',
            description='hello world, this is a part description',
        )

        # Create some stock items
        prices = [(10, 'AUD'), (5, 'USD'), (2, 'CAD')]

        for price, currency in prices:
            stock.models.StockItem.objects.create(
                part=p,
                quantity=10,
                purchase_price=price,
                purchase_price_currency=currency,
            )

        # Ensure that initially, stock item pricing is disabled
        set_global_setting('PRICING_USE_STOCK_PRICING', False, None)

        pricing = p.pricing
        pricing.update_pricing()

        # Check that stock item pricing data is not used
        self.assertIsNone(pricing.purchase_cost_min)
        self.assertIsNone(pricing.purchase_cost_max)
        self.assertIsNone(pricing.overall_min)
        self.assertIsNone(pricing.overall_max)

        # Turn on stock pricing
        set_global_setting('PRICING_USE_STOCK_PRICING', True, None)

        pricing.update_pricing()

        self.assertIsNotNone(pricing.purchase_cost_min)
        self.assertIsNotNone(pricing.purchase_cost_max)

        self.assertEqual(pricing.overall_min, Money(1.176471, 'USD'))
        self.assertEqual(pricing.overall_max, Money(6.666667, 'USD'))

    @override_settings(TESTING_PRICING=True)
    def test_bom_pricing(self):
        """Unit test for BOM pricing calculations."""
        pricing = self.part.pricing

        self.assertIsNone(pricing.bom_cost_min)
        self.assertIsNone(pricing.bom_cost_max)

        currency = 'AUD'

        # Create pricing out of order, to ensure min/max values are calculated correctly
        for ii in range(5):
            # Create a new part for the BOM
            sub_part = part.models.Part.objects.create(
                name=f'Sub Part {ii}',
                description='A sub part for use in a BOM',
                component=True,
                assembly=False,
            )

            # Create some overall pricing
            sub_part_pricing = sub_part.pricing

            # Manually override internal price
            sub_part_pricing.internal_cost_min = Money(2 * (ii + 1), currency)
            sub_part_pricing.internal_cost_max = Money(3 * (ii + 1), currency)
            sub_part_pricing.save()

            part.models.BomItem.objects.create(
                part=self.part, sub_part=sub_part, quantity=5
            )

            # Check that the values have been updated correctly
            self.assertEqual(pricing.currency, 'USD')

        # Price range should have been automatically updated
        self.part.refresh_from_db()
        pricing = self.part.pricing

        expected_min = 100
        expected_max = 150

        # Final overall pricing checks
        self.assertEqual(pricing.overall_min, Money(expected_min, 'USD'))
        self.assertEqual(pricing.overall_max, Money(expected_max, 'USD'))

    @override_settings(TESTING_PRICING=True)
    def test_purchase_pricing(self):
        """Unit tests for historical purchase pricing."""
        self.create_price_breaks()

        pricing = self.part.pricing

        # Pre-calculation, pricing should be null

        self.assertIsNone(pricing.purchase_cost_min)
        self.assertIsNone(pricing.purchase_cost_max)

        # Generate some purchase orders
        po = order.models.PurchaseOrder.objects.create(
            supplier=self.supplier_2, reference='PO-009'
        )

        # Add some line items to the order

        # $5 AUD each @ 2.5m per unit = $2 AUD per metre
        line_1 = po.add_line_item(
            self.sp_2, quantity=10, purchase_price=Money(5, 'AUD')
        )

        # $3 CAD each @ 10 inches per unit = $0.3 CAD per inch = $11.81 CAD per metre
        line_2 = po.add_line_item(self.sp_3, quantity=5, purchase_price=Money(3, 'CAD'))

        pricing.update_purchase_cost()

        # Cost is still null, as the order is not complete
        self.assertIsNone(pricing.purchase_cost_min)
        self.assertIsNone(pricing.purchase_cost_max)

        po.status = PurchaseOrderStatus.COMPLETE.value
        po.save()

        pricing.update_purchase_cost()

        # Cost is still null, as the lines have not been received
        self.assertIsNone(pricing.purchase_cost_min)
        self.assertIsNone(pricing.purchase_cost_max)

        # Mark items as received
        line_1.received = 4
        line_1.save()

        line_2.received = 5
        line_2.save()

        pricing.update_purchase_cost()

        min_cost_aud = convert_money(pricing.purchase_cost_min, 'AUD')
        max_cost_cad = convert_money(pricing.purchase_cost_max, 'CAD')

        # Min cost in AUD = $2 AUD per metre
        self.assertAlmostEqual(float(min_cost_aud.amount), 2, places=2)

        # Min cost in USD
        self.assertAlmostEqual(
            float(pricing.purchase_cost_min.amount), 1.3333, places=2
        )

        # Max cost in CAD = $11.81 CAD per metre
        self.assertAlmostEqual(float(max_cost_cad.amount), 11.81, places=2)

        # Max cost in USD
        self.assertAlmostEqual(float(pricing.purchase_cost_max.amount), 6.95, places=2)

    @override_settings(TESTING_PRICING=True)
    def test_delete_with_pricing(self):
        """Test for deleting a part which has pricing information."""
        # Create some pricing data
        self.create_price_breaks()

        # Check that pricing does exist
        pricing = self.part.pricing

        pricing.update_pricing()
        pricing.save()

        self.assertIsNotNone(pricing.overall_min)
        self.assertIsNotNone(pricing.overall_max)

        self.part.active = False
        self.part.save()

        # Remove the part from the database
        self.part.delete()

        # Check that the pricing was removed also
        with self.assertRaises(part.models.PartPricing.DoesNotExist):
            pricing.refresh_from_db()

    @override_settings(TESTING_PRICING=True)
    def test_delete_without_pricing(self):
        """Test that we can delete a part which does not have pricing information."""
        pricing = self.part.pricing

        self.assertIsNone(pricing.pk)

        self.part.active = False
        self.part.save()

        self.part.delete()

        # Check that part was actually deleted
        with self.assertRaises(part.models.Part.DoesNotExist):
            self.part.refresh_from_db()

    @override_settings(TESTING_PRICING=True)
    def test_check_missing_pricing(self):
        """Tests for check_missing_pricing background task.

        Calling the check_missing_pricing task should:
        - Create PartPricing objects where there are none
        - Schedule pricing calculations for the newly created PartPricing objects
        """
        from part.tasks import check_missing_pricing

        # Create some parts
        for ii in range(100):
            part.models.Part.objects.create(
                name=f'Part_{ii}', description='A test part'
            )

        # Ensure there is no pricing data
        part.models.PartPricing.objects.all().delete()

        check_missing_pricing()

        # Check that PartPricing objects have been created
        self.assertEqual(part.models.PartPricing.objects.count(), 101)

    @override_settings(TESTING_PRICING=True)
    def test_delete_part_with_stock_items(self):
        """Test deleting a part instance with stock items.

        This is to test a specific edge condition which was discovered that caused an IntegrityError.
        Ref: https://github.com/inventree/InvenTree/issues/4419

        Essentially a series of on_delete listeners caused a new PartPricing object to be created,
        but it pointed to a Part instance which was slated to be deleted inside an atomic transaction.
        """
        p = part.models.Part.objects.create(
            name='my part', description='my part description', active=False
        )

        # Create some stock items
        for _idx in range(3):
            stock.models.StockItem.objects.create(
                part=p, quantity=10, purchase_price=Money(10, 'USD')
            )

        # Manually schedule a pricing update (does not happen automatically in testing)
        p.schedule_pricing_update(create=True)

        # Check that a PartPricing object exists
        self.assertTrue(part.models.PartPricing.objects.filter(part=p).exists())

        # Delete the part
        p.delete()

        # Check that the PartPricing object has been deleted
        self.assertFalse(part.models.PartPricing.objects.filter(part=p).exists())

        # Try to update pricing (should fail gracefully as the Part has been deleted)
        p.schedule_pricing_update(create=False)
        self.assertFalse(part.models.PartPricing.objects.filter(part=p).exists())

    @override_settings(TESTING_PRICING=True)
    def test_multi_level_bom(self):
        """Test that pricing for multi-level BOMs is calculated correctly."""
        # Create some parts
        A1 = part.models.Part.objects.create(
            name='A1', description='A1', assembly=True, component=True
        )
        B1 = part.models.Part.objects.create(
            name='B1', description='B1', assembly=True, component=True
        )
        C1 = part.models.Part.objects.create(
            name='C1', description='C1', assembly=True, component=True
        )
        D1 = part.models.Part.objects.create(
            name='D1', description='D1', assembly=True, component=True
        )
        D2 = part.models.Part.objects.create(
            name='D2', description='D2', assembly=True, component=True
        )
        D3 = part.models.Part.objects.create(
            name='D3', description='D3', assembly=True, component=True
        )

        # BOM Items
        part.models.BomItem.objects.create(part=A1, sub_part=B1, quantity=10)
        part.models.BomItem.objects.create(part=B1, sub_part=C1, quantity=2)
        part.models.BomItem.objects.create(part=C1, sub_part=D1, quantity=3)
        part.models.BomItem.objects.create(part=C1, sub_part=D2, quantity=4)
        part.models.BomItem.objects.create(part=C1, sub_part=D3, quantity=5)

        # Pricing data (only for low-level D parts)
        P1 = D1.pricing
        P1.override_min = 4.50
        P1.override_max = 5.50
        P1.save()
        P1.update_pricing()

        P2 = D2.pricing
        P2.override_min = 6.50
        P2.override_max = 7.50
        P2.save()
        P2.update_pricing()

        P3 = D3.pricing
        P3.override_min = 8.50
        P3.override_max = 9.50
        P3.save()
        P3.update_pricing()

        # Simple checks for low-level BOM items
        self.assertEqual(D1.pricing.overall_min, Money(4.50, 'USD'))
        self.assertEqual(D1.pricing.overall_max, Money(5.50, 'USD'))

        self.assertEqual(D2.pricing.overall_min, Money(6.50, 'USD'))
        self.assertEqual(D2.pricing.overall_max, Money(7.50, 'USD'))

        self.assertEqual(D3.pricing.overall_min, Money(8.50, 'USD'))
        self.assertEqual(D3.pricing.overall_max, Money(9.50, 'USD'))

        # Calculate pricing for "C" level part
        c_min = 3 * 4.50 + 4 * 6.50 + 5 * 8.50
        c_max = 3 * 5.50 + 4 * 7.50 + 5 * 9.50

        self.assertEqual(C1.pricing.overall_min, Money(c_min, 'USD'))
        self.assertEqual(C1.pricing.overall_max, Money(c_max, 'USD'))

        # Calculate pricing for "A" and "B" level parts
        b_min = 2 * c_min
        b_max = 2 * c_max

        a_min = 10 * b_min
        a_max = 10 * b_max

        self.assertEqual(B1.pricing.overall_min, Money(b_min, 'USD'))
        self.assertEqual(B1.pricing.overall_max, Money(b_max, 'USD'))

        self.assertEqual(A1.pricing.overall_min, Money(a_min, 'USD'))
        self.assertEqual(A1.pricing.overall_max, Money(a_max, 'USD'))
