"""Unit tests for the models in the 'company' app"""

import os
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from part.models import Part

from .models import (
    Address,
    Company,
    Contact,
    ManufacturerPart,
    SupplierPart,
    rename_company_image,
)


class CompanySimpleTest(TestCase):
    """Unit tests for the Company model"""

    fixtures = [
        'company',
        'category',
        'part',
        'location',
        'bom',
        'manufacturer_part',
        'supplier_part',
        'price_breaks',
    ]

    @classmethod
    def setUpTestData(cls):
        """Perform initialization for the tests in this class"""
        super().setUpTestData()

        Company.objects.create(
            name='ABC Co.',
            description='Seller of ABC products',
            website='www.abc-sales.com',
            is_customer=False,
            is_supplier=True,
        )

        cls.acme0001 = SupplierPart.objects.get(SKU='ACME0001')
        cls.acme0002 = SupplierPart.objects.get(SKU='ACME0002')
        cls.zerglphs = SupplierPart.objects.get(SKU='ZERGLPHS')
        cls.zergm312 = SupplierPart.objects.get(SKU='ZERGM312')

    def test_company_model(self):
        """Tests for the company model data"""
        c = Company.objects.get(name='ABC Co.')
        self.assertEqual(c.name, 'ABC Co.')
        self.assertEqual(str(c), 'ABC Co. - Seller of ABC products')

    def test_company_url(self):
        """Test the detail URL for a company"""
        c = Company.objects.get(pk=1)
        self.assertEqual(c.get_absolute_url(), '/company/1/')

    def test_image_renamer(self):
        """Test the company image upload functionality"""
        c = Company.objects.get(pk=1)
        rn = rename_company_image(c, 'test.png')
        self.assertEqual(rn, 'company_images' + os.path.sep + 'company_1_img.png')

        rn = rename_company_image(c, 'test2')
        self.assertEqual(rn, 'company_images' + os.path.sep + 'company_1_img')

    def test_price_breaks(self):
        """Unit tests for price breaks"""
        self.assertTrue(self.acme0001.has_price_breaks)
        self.assertTrue(self.acme0002.has_price_breaks)
        self.assertTrue(self.zergm312.has_price_breaks)
        self.assertFalse(self.zerglphs.has_price_breaks)

        self.assertEqual(self.acme0001.price_breaks.count(), 3)
        self.assertEqual(self.acme0002.price_breaks.count(), 2)
        self.assertEqual(self.zerglphs.price_breaks.count(), 0)
        self.assertEqual(self.zergm312.price_breaks.count(), 2)

    def test_quantity_pricing(self):
        """Simple test for quantity pricing."""
        p = self.acme0001.get_price
        self.assertEqual(p(1), 10)
        self.assertEqual(p(4), 40)
        self.assertEqual(p(11), 82.5)
        self.assertEqual(p(23), 172.5)
        self.assertEqual(p(100), 350)

        p = self.acme0002.get_price
        self.assertEqual(p(0.5), 3.5)
        self.assertEqual(p(1), 7)
        self.assertEqual(p(2), 14)
        self.assertEqual(p(5), 35)
        self.assertEqual(p(45), 315)
        self.assertEqual(p(55), 68.75)

    def test_part_pricing(self):
        """Unit tests for supplier part pricing"""
        m2x4 = Part.objects.get(name='M2x4 LPHS')

        self.assertEqual(m2x4.get_price_info(5.5), '38.5 - 41.25')
        self.assertEqual(m2x4.get_price_info(10), '70 - 75')
        self.assertEqual(m2x4.get_price_info(100), '125 - 350')

        pmin, pmax = m2x4.get_price_range(5)
        self.assertEqual(pmin, 35)
        self.assertEqual(pmax, 37.5)

        m3x12 = Part.objects.get(name='M3x12 SHCS')

        self.assertEqual(m3x12.get_price_info(0.3), Decimal('2.4'))
        self.assertEqual(m3x12.get_price_info(3), Decimal('24'))
        self.assertIsNotNone(m3x12.get_price_info(50))

    def test_currency_validation(self):
        """Test validation for currency selection."""
        # Create a company with a valid currency code (should pass)
        company = Company.objects.create(
            name='Test', description='Toast', currency='AUD'
        )

        company.full_clean()

        # Create a company with an invalid currency code (should fail)
        company = Company.objects.create(
            name='test', description='Toasty', currency='XZY'
        )

        with self.assertRaises(ValidationError):
            company.full_clean()

    def test_metadata(self):
        """Unit tests for the metadata field."""
        p = Company.objects.first()
        self.assertIn(p.metadata, [None, {}])

        self.assertIsNone(p.get_metadata('test'))
        self.assertEqual(p.get_metadata('test', backup_value=123), 123)

        # Test update via the set_metadata() method
        p.set_metadata('test', 3)
        self.assertEqual(p.get_metadata('test'), 3)

        for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
            p.set_metadata(k, k)

        self.assertEqual(len(p.metadata.keys()), 4)


class ContactSimpleTest(TestCase):
    """Unit tests for the Contact model"""

    def setUp(self):
        """Initialization for the tests in this class"""
        # Create a simple company
        self.c = Company.objects.create(
            name='Test Corp.', description='We make stuff good'
        )

        # Add some contacts
        Contact.objects.create(name='Joe Smith', company=self.c)
        Contact.objects.create(name='Fred Smith', company=self.c)
        Contact.objects.create(name='Sally Smith', company=self.c)

    def test_exists(self):
        """Test that contacts exist"""
        self.assertEqual(Contact.objects.count(), 3)

    def test_delete(self):
        """Test deletion of a Contact instance"""
        # Remove the parent company
        Company.objects.get(pk=self.c.pk).delete()
        self.assertEqual(Contact.objects.count(), 0)


class AddressTest(TestCase):
    """Unit tests for the Address model"""

    def setUp(self):
        """Initialization for the tests in this class"""
        # Create a simple company
        self.c = Company.objects.create(
            name='Test Corp.', description='We make stuff good'
        )

    def test_create(self):
        """Test that object creation with only company supplied is successful"""
        Address.objects.create(company=self.c)
        self.assertEqual(Address.objects.count(), 1)

    def test_delete(self):
        """Test Address deletion"""
        addr = Address.objects.create(company=self.c)
        addr.delete()
        self.assertEqual(Address.objects.count(), 0)

    def test_primary_constraint(self):
        """Test that there can only be one company-'primary=true' pair"""
        Address.objects.create(company=self.c, primary=True)
        Address.objects.create(company=self.c, primary=False)

        self.assertEqual(Address.objects.count(), 2)

        self.assertTrue(Address.objects.first().primary)

        # Create another address, specify *this* as primary
        Address.objects.create(company=self.c, primary=True)

        self.assertEqual(Address.objects.count(), 3)
        self.assertFalse(Address.objects.first().primary)
        self.assertTrue(Address.objects.last().primary)

    def test_first_address_is_primary(self):
        """Test that first address related to company is always set to primary"""
        addr = Address.objects.create(company=self.c)
        self.assertTrue(addr.primary)

    def test_model_str(self):
        """Test value of __str__"""
        t = 'Test address'
        l1 = 'Busy street 56'
        l2 = 'Red building'
        pcd = '12345'
        pct = 'City'
        pv = 'Province'
        cn = 'COUNTRY'
        addr = Address.objects.create(
            company=self.c,
            title=t,
            line1=l1,
            line2=l2,
            postal_code=pcd,
            postal_city=pct,
            province=pv,
            country=cn,
        )
        self.assertEqual(str(addr), f'{l1}, {l2}, {pcd}, {pct}, {pv}, {cn}')

        addr2 = Address.objects.create(
            company=self.c, title=t, line1=l1, postal_code=pcd
        )

        self.assertEqual(str(addr2), f'{l1}, {pcd}')


class ManufacturerPartSimpleTest(TestCase):
    """Unit tests for the ManufacturerPart model"""

    fixtures = ['category', 'company', 'location', 'part', 'manufacturer_part']

    def setUp(self):
        """Initialization for the unit tests in this class"""
        # Create a manufacturer part
        self.part = Part.objects.get(pk=1)
        manufacturer = Company.objects.get(pk=1)

        self.mp = ManufacturerPart.create(
            part=self.part,
            manufacturer=manufacturer,
            mpn='PART_NUMBER',
            description='THIS IS A MANUFACTURER PART',
        )

        # Create a supplier part
        supplier = Company.objects.get(pk=5)
        supplier_part = SupplierPart.objects.create(
            part=self.part, supplier=supplier, SKU='SKU_TEST'
        )

        supplier_part.save()

    def test_exists(self):
        """That that a ManufacturerPart has been created"""
        self.assertEqual(ManufacturerPart.objects.count(), 4)

        # Check that manufacturer part was created from supplier part creation
        manufacturer_parts = ManufacturerPart.objects.filter(manufacturer=1)
        self.assertEqual(manufacturer_parts.count(), 1)

    def test_delete(self):
        """Test deletion of a ManufacturerPart"""
        Part.objects.get(pk=self.part.id).delete()
        # Check that ManufacturerPart was deleted
        self.assertEqual(ManufacturerPart.objects.count(), 3)

    def test_metadata(self):
        """Unit tests for the metadata field."""
        for model in [ManufacturerPart, SupplierPart]:
            p = model.objects.first()
            self.assertIn(p.metadata, [None, {}])

            self.assertIsNone(p.get_metadata('test'))
            self.assertEqual(p.get_metadata('test', backup_value=123), 123)

            # Test update via the set_metadata() method
            p.set_metadata('test', 3)
            self.assertEqual(p.get_metadata('test'), 3)

            for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
                p.set_metadata(k, k)

            self.assertEqual(len(p.metadata.keys()), 4)
