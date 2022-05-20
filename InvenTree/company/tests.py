import os
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from part.models import Part

from .models import (Company, Contact, ManufacturerPart, SupplierPart,
                     rename_company_image)


class CompanySimpleTest(TestCase):

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

    def setUp(self):
        Company.objects.create(name='ABC Co.',
                               description='Seller of ABC products',
                               website='www.abc-sales.com',
                               address='123 Sales St.',
                               is_customer=False,
                               is_supplier=True)

        self.acme0001 = SupplierPart.objects.get(SKU='ACME0001')
        self.acme0002 = SupplierPart.objects.get(SKU='ACME0002')
        self.zerglphs = SupplierPart.objects.get(SKU='ZERGLPHS')
        self.zergm312 = SupplierPart.objects.get(SKU='ZERGM312')

    def test_company_model(self):
        c = Company.objects.get(name='ABC Co.')
        self.assertEqual(c.name, 'ABC Co.')
        self.assertEqual(str(c), 'ABC Co. - Seller of ABC products')

    def test_company_url(self):
        c = Company.objects.get(pk=1)
        self.assertEqual(c.get_absolute_url(), '/company/1/')

    def test_image_renamer(self):
        c = Company.objects.get(pk=1)
        rn = rename_company_image(c, 'test.png')
        self.assertEqual(rn, 'company_images' + os.path.sep + 'company_1_img.png')

        rn = rename_company_image(c, 'test2')
        self.assertEqual(rn, 'company_images' + os.path.sep + 'company_1_img')

    def test_part_count(self):

        acme = Company.objects.get(pk=1)
        appel = Company.objects.get(pk=2)
        zerg = Company.objects.get(pk=3)

        self.assertTrue(acme.has_parts)
        self.assertEqual(acme.supplied_part_count, 4)

        self.assertTrue(appel.has_parts)
        self.assertEqual(appel.supplied_part_count, 4)

        self.assertTrue(zerg.has_parts)
        self.assertEqual(zerg.supplied_part_count, 2)

    def test_price_breaks(self):

        self.assertTrue(self.acme0001.has_price_breaks)
        self.assertTrue(self.acme0002.has_price_breaks)
        self.assertTrue(self.zergm312.has_price_breaks)
        self.assertFalse(self.zerglphs.has_price_breaks)

        self.assertEqual(self.acme0001.price_breaks.count(), 3)
        self.assertEqual(self.acme0002.price_breaks.count(), 2)
        self.assertEqual(self.zerglphs.price_breaks.count(), 0)
        self.assertEqual(self.zergm312.price_breaks.count(), 2)

    def test_quantity_pricing(self):
        """ Simple test for quantity pricing """

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
        m2x4 = Part.objects.get(name='M2x4 LPHS')

        self.assertEqual(m2x4.get_price_info(5.5), "38.5 - 41.25")
        self.assertEqual(m2x4.get_price_info(10), "70 - 75")
        self.assertEqual(m2x4.get_price_info(100), "125 - 350")

        pmin, pmax = m2x4.get_price_range(5)
        self.assertEqual(pmin, 35)
        self.assertEqual(pmax, 37.5)

        m3x12 = Part.objects.get(name='M3x12 SHCS')

        self.assertEqual(m3x12.get_price_info(0.3), Decimal('2.4'))
        self.assertEqual(m3x12.get_price_info(3), Decimal('24'))
        self.assertIsNotNone(m3x12.get_price_info(50))

    def test_currency_validation(self):
        """
        Test validation for currency selection
        """

        # Create a company with a valid currency code (should pass)
        company = Company.objects.create(
            name='Test',
            description='Toast',
            currency='AUD',
        )

        company.full_clean()

        # Create a company with an invalid currency code (should fail)
        company = Company.objects.create(
            name='test',
            description='Toasty',
            currency='XZY',
        )

        with self.assertRaises(ValidationError):
            company.full_clean()


class ContactSimpleTest(TestCase):

    def setUp(self):
        # Create a simple company
        self.c = Company.objects.create(name='Test Corp.', description='We make stuff good')

        # Add some contacts
        Contact.objects.create(name='Joe Smith', company=self.c)
        Contact.objects.create(name='Fred Smith', company=self.c)
        Contact.objects.create(name='Sally Smith', company=self.c)

    def test_exists(self):
        self.assertEqual(Contact.objects.count(), 3)

    def test_delete(self):
        # Remove the parent company
        Company.objects.get(pk=self.c.pk).delete()
        self.assertEqual(Contact.objects.count(), 0)


class ManufacturerPartSimpleTest(TestCase):

    fixtures = [
        'category',
        'company',
        'location',
        'part',
        'manufacturer_part',
    ]

    def setUp(self):
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
            part=self.part,
            supplier=supplier,
            SKU='SKU_TEST',
        )

        supplier_part.save()

    def test_exists(self):
        self.assertEqual(ManufacturerPart.objects.count(), 4)

        # Check that manufacturer part was created from supplier part creation
        manufacturer_parts = ManufacturerPart.objects.filter(manufacturer=1)
        self.assertEqual(manufacturer_parts.count(), 1)

    def test_delete(self):
        # Remove a part
        Part.objects.get(pk=self.part.id).delete()
        # Check that ManufacturerPart was deleted
        self.assertEqual(ManufacturerPart.objects.count(), 3)
