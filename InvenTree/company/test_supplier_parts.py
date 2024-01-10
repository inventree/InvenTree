"""Unit tests specific to the SupplierPart model."""

from decimal import Decimal

from django.core.exceptions import ValidationError

from part.models import Part

from company.models import Company, SupplierPart
from InvenTree.unit_test import InvenTreeTestCase


class SupplierPartPackUnitsTests(InvenTreeTestCase):
    """Unit tests for the SupplierPart pack_quantity field."""

    def test_pack_quantity_dimensionless(self):
        """Test valid values for the 'pack_quantity' field."""
        # Create a part without units (dimensionless)
        part = Part.objects.create(
            name='Test Part', description='Test part description', component=True
        )

        # Create a supplier (company)
        company = Company.objects.create(name='Test Company', is_supplier=True)

        # Create a supplier part for this part
        sp = SupplierPart.objects.create(part=part, supplier=company, SKU='TEST-SKU')

        # All these values are valid for a dimensionless part
        pass_tests = {
            '': 1,
            '1': 1,
            '1.01': 1.01,
            '12.000001': 12.000001,
            '99.99': 99.99,
        }

        # All these values are invalid for a dimensionless part
        fail_tests = ['1.2m', '-1', '0', '0.0', '100 feet', '0 amps']

        for test, expected in pass_tests.items():
            sp.pack_quantity = test
            sp.full_clean()
            self.assertEqual(sp.pack_quantity_native, expected)

        for test in fail_tests:
            sp.pack_quantity = test
            with self.assertRaises(ValidationError):
                sp.full_clean()

    def test_pack_quantity(self):
        """Test pack_quantity for a part with a specified dimension."""
        # Create a part with units 'm'
        part = Part.objects.create(
            name='Test Part',
            description='Test part description',
            component=True,
            units='m',
        )

        # Create a supplier (company)
        company = Company.objects.create(name='Test Company', is_supplier=True)

        # Create a supplier part for this part
        sp = SupplierPart.objects.create(part=part, supplier=company, SKU='TEST-SKU')

        # All these values are valid for a part with dimension 'm'
        pass_tests = {
            '': 1,
            '1': 1,
            '1m': 1,
            '1.01m': 1.01,
            '1.01': 1.01,
            '5 inches': 0.127,
            '27 cm': 0.27,
            '3km': 3000,
            '14 feet': 4.2672,
            '0.5 miles': 804.672,
        }

        # All these values are invalid for a part with dimension 'm'
        # Either the values are invalid, or the units are incompatible
        fail_tests = ['-1', '-1m', '0', '0m', '12 deg', '57 amps', '-12 oz', '17 yaks']

        for test, expected in pass_tests.items():
            sp.pack_quantity = test
            sp.full_clean()
            self.assertEqual(
                round(Decimal(sp.pack_quantity_native), 10),
                round(Decimal(str(expected)), 10),
            )

        for test in fail_tests:
            sp.pack_quantity = test
            with self.assertRaises(ValidationError):
                sp.full_clean()
