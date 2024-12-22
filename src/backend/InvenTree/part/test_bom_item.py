"""Unit tests for the BomItem model."""

from decimal import Decimal

import django.core.exceptions as django_exceptions
from django.db import transaction
from django.test import TestCase

import stock.models

from .models import BomItem, BomItemSubstitute, Part


class BomItemTest(TestCase):
    """Class for unit testing BomItem model."""

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
        """Create initial data."""
        super().setUp()

        Part.objects.rebuild()

        self.bob = Part.objects.get(id=100)
        self.orphan = Part.objects.get(name='Orphan')
        self.r1 = Part.objects.get(name='R_2K2_0805')

    def test_str(self):
        """Test the string representation of a BOMItem."""
        b = BomItem.objects.get(id=1)
        self.assertEqual(str(b), '10 x M2x4 LPHS to make BOB | Bob | A2')

    def test_has_bom(self):
        """Test the has_bom attribute."""
        self.assertFalse(self.orphan.has_bom)
        self.assertTrue(self.bob.has_bom)

        self.assertEqual(self.bob.bom_count, 4)

    def test_in_bom(self):
        """Test BOM aggregation."""
        parts = self.bob.getRequiredParts()

        self.assertIn(self.orphan, parts)

        self.assertTrue(self.bob.check_if_part_in_bom(self.orphan))

    def test_used_in(self):
        """Test that the 'used_in_count' attribute is calculated correctly."""
        self.assertEqual(self.bob.used_in_count, 1)
        self.assertEqual(self.orphan.used_in_count, 1)

    def test_self_reference(self):
        """Test that we get an appropriate error when we create a BomItem which points to itself."""
        with self.assertRaises(django_exceptions.ValidationError):
            # A validation error should be raised here
            item = BomItem.objects.create(part=self.bob, sub_part=self.bob, quantity=7)
            item.clean()  # pragma: no cover

    def test_integer_quantity(self):
        """Test integer validation for BomItem."""
        p = Part.objects.create(
            name='test', description='part description', component=True, trackable=True
        )

        # Creation of a BOMItem with a non-integer quantity of a trackable Part should fail
        with self.assertRaises(django_exceptions.ValidationError):
            BomItem.objects.create(part=self.bob, sub_part=p, quantity=21.7)

        # But with an integer quantity, should be fine
        BomItem.objects.create(part=self.bob, sub_part=p, quantity=21)

    def test_overage(self):
        """Test that BOM line overages are calculated correctly."""
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
        """Test BOM item hash encoding."""
        item = BomItem.objects.get(part=100, sub_part=50)

        h1 = item.get_item_hash()

        # Change data - the hash must change
        item.quantity += 1

        h2 = item.get_item_hash()

        item.validate_hash()

        self.assertNotEqual(h1, h2)

    def test_pricing(self):
        """Test BOM pricing."""
        self.bob.get_price(1)
        self.assertEqual(
            self.bob.get_bom_price_range(1, internal=True),
            (Decimal(29.5), Decimal(89.5)),
        )
        # remove internal price for R_2K2_0805
        self.r1.internal_price_breaks.delete()
        self.assertEqual(
            self.bob.get_bom_price_range(1, internal=True),
            (Decimal(27.5), Decimal(87.5)),
        )

    def test_substitutes(self):
        """Tests for BOM item substitutes."""
        # We will make some substitute parts for the "orphan" part
        bom_item = BomItem.objects.get(part=self.bob, sub_part=self.orphan)

        # No substitute parts available
        self.assertEqual(bom_item.substitutes.count(), 0)

        subs = []

        for ii in range(5):
            # Create a new part
            sub_part = Part.objects.create(
                name=f'Orphan {ii}',
                description='A substitute part for the orphan part',
                component=True,
                is_template=False,
                assembly=False,
            )

            subs.append(sub_part)

            # Link it as a substitute part
            BomItemSubstitute.objects.create(bom_item=bom_item, part=sub_part)

            # Try to link it again (this should fail as it is a duplicate substitute)
            with self.assertRaises(django_exceptions.ValidationError):
                with transaction.atomic():
                    BomItemSubstitute.objects.create(bom_item=bom_item, part=sub_part)

        # There should be now 5 substitute parts available
        self.assertEqual(bom_item.substitutes.count(), 5)

        # Try to create a substitute which points to the same sub-part (should fail)
        with self.assertRaises(django_exceptions.ValidationError):
            BomItemSubstitute.objects.create(bom_item=bom_item, part=self.orphan)

        # Remove one substitute part
        bom_item.substitutes.last().delete()

        self.assertEqual(bom_item.substitutes.count(), 4)

        for sub in subs:
            sub.active = False
            sub.save()
            sub.delete()

        # The substitution links should have been automatically removed
        self.assertEqual(bom_item.substitutes.count(), 0)

    def test_consumable(self):
        """Tests for the 'consumable' BomItem field."""
        # Create an assembly part
        assembly = Part.objects.create(
            name='An assembly', description='Made with parts', assembly=True
        )

        # No BOM information initially
        self.assertEqual(assembly.can_build, 0)

        # Create some component items
        c1 = Part.objects.create(
            name='C1', description='Part C1 - this is just the part description'
        )
        c2 = Part.objects.create(
            name='C2', description='Part C2 - this is just the part description'
        )
        c3 = Part.objects.create(
            name='C3', description='Part C3 - this is just the part description'
        )
        c4 = Part.objects.create(
            name='C4', description='Part C4 - this is just the part description'
        )

        for p in [c1, c2, c3, c4]:
            # Ensure we have stock
            stock.models.StockItem.objects.create(part=p, quantity=1000)

        # Create some BOM items
        BomItem.objects.create(part=assembly, sub_part=c1, quantity=10)

        self.assertEqual(assembly.can_build, 100)

        BomItem.objects.create(part=assembly, sub_part=c2, quantity=50, consumable=True)

        # A 'consumable' BomItem does not alter the can_build calculation
        self.assertEqual(assembly.can_build, 100)

        BomItem.objects.create(part=assembly, sub_part=c3, quantity=50)

        self.assertEqual(assembly.can_build, 20)

    def test_metadata(self):
        """Unit tests for the metadata field."""
        for model in [BomItem]:
            p = model.objects.first()

            self.assertIsNone(p.get_metadata('test'))
            self.assertEqual(p.get_metadata('test', backup_value=123), 123)

            # Test update via the set_metadata() method
            p.set_metadata('test', 3)
            self.assertEqual(p.get_metadata('test'), 3)

            for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
                p.set_metadata(k, k)

            self.assertEqual(len(p.metadata.keys()), 4)

    def test_invalid_bom(self):
        """Test that ValidationError is correctly raised for an invalid BOM item."""
        # First test: A BOM item which points to itself
        with self.assertRaises(django_exceptions.ValidationError):
            BomItem.objects.create(part=self.bob, sub_part=self.bob, quantity=1)

        # Second test: A recursive BOM
        part_a = Part.objects.create(
            name='Part A',
            description='A part which is called A',
            assembly=True,
            is_template=True,
            component=True,
        )
        part_b = Part.objects.create(
            name='Part B',
            description='A part which is called B',
            assembly=True,
            component=True,
        )
        part_c = Part.objects.create(
            name='Part C',
            description='A part which is called C',
            assembly=True,
            component=True,
        )

        BomItem.objects.create(part=part_a, sub_part=part_b, quantity=10)
        BomItem.objects.create(part=part_b, sub_part=part_c, quantity=10)

        with self.assertRaises(django_exceptions.ValidationError):
            BomItem.objects.create(part=part_c, sub_part=part_a, quantity=10)

        with self.assertRaises(django_exceptions.ValidationError):
            BomItem.objects.create(part=part_c, sub_part=part_b, quantity=10)

        # Third test: A recursive BOM with a variant part
        part_v = Part.objects.create(
            name='Part V',
            description='A part which is called V',
            variant_of=part_a,
            assembly=True,
            component=True,
        )

        with self.assertRaises(django_exceptions.ValidationError):
            BomItem.objects.create(part=part_a, sub_part=part_v, quantity=10)

        with self.assertRaises(django_exceptions.ValidationError):
            BomItem.objects.create(part=part_v, sub_part=part_a, quantity=10)

    def test_locked_assembly(self):
        """Test that BomItem objects work correctly for a 'locked' assembly."""
        assembly = Part.objects.create(
            name='Assembly2', description='An assembly part', assembly=True
        )

        sub_part = Part.objects.create(
            name='SubPart1', description='A sub-part', component=True
        )

        # Initially, the assembly is not locked
        self.assertFalse(assembly.locked)

        # Create a BOM item for the assembly
        bom_item = BomItem.objects.create(part=assembly, sub_part=sub_part, quantity=1)

        # Lock the assembly
        assembly.locked = True
        assembly.save()

        # Try to edit the BOM item
        with self.assertRaises(django_exceptions.ValidationError):
            bom_item.quantity = 10
            bom_item.save()

        # Try to delete the BOM item
        with self.assertRaises(django_exceptions.ValidationError):
            bom_item.delete()

        # Try to create a new BOM item
        with self.assertRaises(django_exceptions.ValidationError):
            BomItem.objects.create(part=assembly, sub_part=sub_part, quantity=1)

        # Unlock the part and try again
        assembly.locked = False
        assembly.save()

        # Create a new BOM item
        bom_item = BomItem.objects.create(part=assembly, sub_part=sub_part, quantity=1)

        # Edit the new BOM item
        bom_item.quantity = 10
        bom_item.save()

        # Delete the new BOM item
        bom_item.delete()
