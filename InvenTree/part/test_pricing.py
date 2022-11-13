"""Unit tests for Part pricing calculations"""

from django.core.exceptions import ObjectDoesNotExist

from djmoney.contrib.exchange.models import ExchangeBackend, Rate
from djmoney.money import Money

import common.models
import common.settings
import company.models
import order.models
import part.models
from InvenTree.helpers import InvenTreeTestCase
from InvenTree.status_codes import PurchaseOrderStatus


class PartPricingTests(InvenTreeTestCase):
    """Unit tests for part pricing calculations"""

    def generate_exchange_rates(self):
        """Generate some exchange rates to work with"""

        rates = {
            'AUD': 1.5,
            'CAD': 1.7,
            'GBP': 0.9,
            'USD': 1.0,
        }

        # Create a dummy backend
        ExchangeBackend.objects.create(
            name='InvenTreeExchange',
            base_currency='USD',
        )

        backend = ExchangeBackend.objects.get(name='InvenTreeExchange')

        for currency, rate in rates.items():
            Rate.objects.create(
                currency=currency,
                value=rate,
                backend=backend,
            )

    def setUp(self):
        """Setup routines"""

        self.generate_exchange_rates()

        # Create a new part for performing pricing calculations
        self.part = part.models.Part.objects.create(
            name='PP',
            description='A part with pricing',
            assembly=True
        )

        return super().setUp()

    def create_price_breaks(self):
        """Create some price breaks for the part, in various currencies"""

        # First supplier part (CAD)
        self.supplier_1 = company.models.Company.objects.create(
            name='Supplier 1',
            is_supplier=True
        )

        self.sp_1 = company.models.SupplierPart.objects.create(
            supplier=self.supplier_1,
            part=self.part,
            SKU='SUP_1',
        )

        company.models.SupplierPriceBreak.objects.create(
            part=self.sp_1,
            quantity=1,
            price=10.4,
            price_currency='CAD',
        )

        # Second supplier part (AUD)
        self.supplier_2 = company.models.Company.objects.create(
            name='Supplier 2',
            is_supplier=True
        )

        self.sp_2 = company.models.SupplierPart.objects.create(
            supplier=self.supplier_2,
            part=self.part,
            SKU='SUP_2',
            pack_size=2.5,
        )

        self.sp_3 = company.models.SupplierPart.objects.create(
            supplier=self.supplier_2,
            part=self.part,
            SKU='SUP_3',
            pack_size=10
        )

        company.models.SupplierPriceBreak.objects.create(
            part=self.sp_2,
            quantity=5,
            price=7.555,
            price_currency='AUD',
        )

        # Third supplier part (GBP)
        company.models.SupplierPriceBreak.objects.create(
            part=self.sp_2,
            quantity=10,
            price=4.55,
            price_currency='GBP',
        )

    def test_pricing_data(self):
        """Test link between Part and PartPricing model"""

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
        """Ensure that conversion behaves properly with missing rates"""
        ...

    def test_simple(self):
        """Tests for hard-coded values"""

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

    def test_supplier_part_pricing(self):
        """Test for supplier part pricing"""

        pricing = self.part.pricing

        # Initially, no information (not yet calculated)
        self.assertIsNone(pricing.supplier_price_min)
        self.assertIsNone(pricing.supplier_price_max)
        self.assertIsNone(pricing.overall_min)
        self.assertIsNone(pricing.overall_max)

        # Creating price breaks will cause the pricing to be updated
        self.create_price_breaks()

        pricing.update_pricing()

        self.assertEqual(pricing.overall_min, Money('2.014667', 'USD'))
        self.assertEqual(pricing.overall_max, Money('6.117647', 'USD'))

        # Delete all supplier parts and re-calculate
        self.part.supplier_parts.all().delete()
        pricing.update_pricing()
        pricing.refresh_from_db()

        self.assertIsNone(pricing.supplier_price_min)
        self.assertIsNone(pricing.supplier_price_max)

    def test_internal_pricing(self):
        """Tests for internal price breaks"""

        # Ensure internal pricing is enabled
        common.models.InvenTreeSetting.set_setting('PART_INTERNAL_PRICE', True, None)

        pricing = self.part.pricing

        # Initially, no internal price breaks
        self.assertIsNone(pricing.internal_cost_min)
        self.assertIsNone(pricing.internal_cost_max)

        currency = common.settings.currency_code_default()

        for ii in range(5):
            # Let's add some internal price breaks
            part.models.PartInternalPriceBreak.objects.create(
                part=self.part,
                quantity=ii + 1,
                price=10 - ii,
                price_currency=currency
            )

            pricing.update_internal_cost()

            # Expected money value
            m_expected = Money(10 - ii, currency)

            # Minimum cost should keep decreasing as we add more items
            self.assertEqual(pricing.internal_cost_min, m_expected)
            self.assertEqual(pricing.overall_min, m_expected)

            # Maximum cost should stay the same
            self.assertEqual(pricing.internal_cost_max, Money(10, currency))
            self.assertEqual(pricing.overall_max, Money(10, currency))

    def test_bom_pricing(self):
        """Unit test for BOM pricing calculations"""

        pricing = self.part.pricing

        self.assertIsNone(pricing.bom_cost_min)
        self.assertIsNone(pricing.bom_cost_max)

        currency = 'AUD'

        for ii in range(10):
            # Create a new part for the BOM
            sub_part = part.models.Part.objects.create(
                name=f"Sub Part {ii}",
                description="A sub part for use in a BOM",
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
                part=self.part,
                sub_part=sub_part,
                quantity=5,
            )

            pricing.update_bom_cost()

            # Check that the values have been updated correctly
            self.assertEqual(pricing.currency, 'USD')

        # Final overall pricing checks
        self.assertEqual(pricing.overall_min, Money('366.666665', 'USD'))
        self.assertEqual(pricing.overall_max, Money('550', 'USD'))

    def test_purchase_pricing(self):
        """Unit tests for historical purchase pricing"""

        self.create_price_breaks()

        pricing = self.part.pricing

        # Pre-calculation, pricing should be null

        self.assertIsNone(pricing.purchase_cost_min)
        self.assertIsNone(pricing.purchase_cost_max)

        # Generate some purchase orders
        po = order.models.PurchaseOrder.objects.create(
            supplier=self.supplier_2,
            reference='PO-009',
        )

        # Add some line items to the order

        # $5 AUD each
        line_1 = po.add_line_item(self.sp_2, quantity=10, purchase_price=Money(5, 'AUD'))

        # $30 CAD each (but pack_size is 10, so really $3 CAD each)
        line_2 = po.add_line_item(self.sp_3, quantity=5, purchase_price=Money(30, 'CAD'))

        pricing.update_purchase_cost()

        # Cost is still null, as the order is not complete
        self.assertIsNone(pricing.purchase_cost_min)
        self.assertIsNone(pricing.purchase_cost_max)

        po.status = PurchaseOrderStatus.COMPLETE
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

        self.assertEqual(pricing.purchase_cost_min, Money('1.333333', 'USD'))
        self.assertEqual(pricing.purchase_cost_max, Money('1.764706', 'USD'))
