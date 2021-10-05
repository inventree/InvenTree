from django.test import TestCase
import django.core.exceptions as django_exceptions
from decimal import Decimal

from .models import Part, BomItem


class BomItemTest(TestCase):

    fixtures = [
        'category',
        'part',
        'location',
        'bom',
        'company',
        'supplier_part',
        'part_pricebreaks',
        'price_breaks',
    ]

    def setUp(self):
        self.bob = Part.objects.get(id=100)
        self.orphan = Part.objects.get(name='Orphan')
        self.r1 = Part.objects.get(name='R_2K2_0805')

    def test_str(self):
        b = BomItem.objects.get(id=1)
        self.assertEqual(str(b), '10 x M2x4 LPHS to make BOB | Bob | A2')

    def test_has_bom(self):
        self.assertFalse(self.orphan.has_bom)
        self.assertTrue(self.bob.has_bom)

        self.assertEqual(self.bob.bom_count, 4)

    def test_in_bom(self):
        parts = self.bob.getRequiredParts()

        self.assertIn(self.orphan, parts)

    # TODO: Tests for multi-level BOMs

    def test_used_in(self):
        self.assertEqual(self.bob.used_in_count, 0)
        self.assertEqual(self.orphan.used_in_count, 1)

    def test_self_reference(self):
        """ Test that we get an appropriate error when we create a BomItem which points to itself """

        with self.assertRaises(django_exceptions.ValidationError):
            # A validation error should be raised here
            item = BomItem.objects.create(part=self.bob, sub_part=self.bob, quantity=7)
            item.clean()

    def test_integer_quantity(self):
        """
        Test integer validation for BomItem
        """

        p = Part.objects.create(name="test", description="d", component=True, trackable=True)

        # Creation of a BOMItem with a non-integer quantity of a trackable Part should fail
        with self.assertRaises(django_exceptions.ValidationError):
            BomItem.objects.create(part=self.bob, sub_part=p, quantity=21.7)

        # But with an integer quantity, should be fine
        BomItem.objects.create(part=self.bob, sub_part=p, quantity=21)

    def test_overage(self):
        """ Test that BOM line overages are calculated correctly """

        item = BomItem.objects.get(part=100, sub_part=50)

        q = 300

        item.quantity = q

        # Test empty overage
        n = item.get_overage_quantity(q)
        self.assertEqual(n, 0)

        # Test improper overage
        item.overage = 'asf234?'
        n = item.get_overage_quantity(q)
        self.assertEqual(n, 0)

        # Test absolute overage
        item.overage = '3'
        n = item.get_overage_quantity(q)
        self.assertEqual(n, 3)

        # Test percentage-based overage
        item.overage = '5.0 % '
        n = item.get_overage_quantity(q)
        self.assertEqual(n, 15)

        # Calculate total required quantity
        # Quantity = 300 (+ 5%)
        # Get quantity required to build B = 10
        # Q * B = 3000 + 5% = 3150
        n = item.get_required_quantity(10)

        self.assertEqual(n, 3150)

    def test_item_hash(self):
        """ Test BOM item hash encoding """

        item = BomItem.objects.get(part=100, sub_part=50)

        h1 = item.get_item_hash()

        # Change data - the hash must change
        item.quantity += 1

        h2 = item.get_item_hash()

        item.validate_hash()

        self.assertNotEqual(h1, h2)

    def test_pricing(self):
        self.bob.get_price(1)
        self.assertEqual(
            self.bob.get_bom_price_range(1, internal=True),
            (Decimal(29.5), Decimal(89.5))
        )
        # remove internal price for R_2K2_0805
        self.r1.internal_price_breaks.delete()
        self.assertEqual(
            self.bob.get_bom_price_range(1, internal=True),
            (Decimal(27.5), Decimal(87.5))
        )
