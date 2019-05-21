from django.test import TestCase

import os

from .models import Company, Contact
from .models import rename_company_image


class CompanySimpleTest(TestCase):

    fixtures = [
        'company',
        'category',
        'part',
        'location',
        'bom',
        'supplier_part',
    ]

    def setUp(self):
        Company.objects.create(name='ABC Co.',
                               description='Seller of ABC products',
                               website='www.abc-sales.com',
                               address='123 Sales St.',
                               is_customer=False,
                               is_supplier=True)

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
        self.assertEqual(acme.part_count, 2)

        self.assertFalse(appel.has_parts)
        self.assertEqual(appel.part_count, 0)

        self.assertTrue(zerg.has_parts)
        self.assertEqual(zerg.part_count, 1)



        # TODO - Add some supplier parts here


class ContactSimpleTest(TestCase):

    def setUp(self):
        # Create a simple company
        c = Company.objects.create(name='Test Corp.', description='We make stuff good')

        # Add some contacts
        Contact.objects.create(name='Joe Smith', company=c)
        Contact.objects.create(name='Fred Smith', company=c)
        Contact.objects.create(name='Sally Smith', company=c)

    def test_exists(self):
        self.assertEqual(Contact.objects.count(), 3)

    def test_delete(self):
        # Remove the parent company
        Company.objects.get(pk=1).delete()
        self.assertEqual(Contact.objects.count(), 0)
