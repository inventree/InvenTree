from django.test import TestCase

import os

from .models import Part
from .models import rename_part_image
from .templatetags import inventree_extras


class TemplateTagTest(TestCase):
    """ Tests for the custom template tag code """

    def test_multiply(self):
        self.assertEqual(inventree_extras.multiply(3, 5), 15)

    def test_version(self):
        self.assertEqual(type(inventree_extras.inventree_version()), str)

    def test_hash(self):
        hash = inventree_extras.inventree_commit()
        self.assertEqual(len(hash), 7)

    def test_github(self):
        self.assertIn('github.com', inventree_extras.inventree_github())


class PartTest(TestCase):
    """ Tests for the Part model """

    fixtures = [
        'category',
        'part',
        'location',
    ]

    def setUp(self):
        self.R1 = Part.objects.get(name='R_2K2_0805')
        self.R2 = Part.objects.get(name='R_4K7_0603')

        self.C1 = Part.objects.get(name='C_22N_0805')

    def test_metadata(self):
        self.assertEqual(self.R1.name, 'R_2K2_0805')
        self.assertEqual(self.R1.get_absolute_url(), '/part/3/')

    def test_category(self):
        self.assertEqual(str(self.C1.category), 'Electronics/Capacitors')

        orphan = Part.objects.get(name='Orphan')
        self.assertIsNone(orphan.category)
        self.assertEqual(orphan.category_path, '')

    def test_rename_img(self):
        img = rename_part_image(self.R1, 'hello.png')
        self.assertEqual(img, os.path.join('part_images', 'part_3_img.png'))

        img = rename_part_image(self.R2, 'test')
        self.assertEqual(img, os.path.join('part_images', 'part_4_img'))

    def test_stock(self):
        # No stock of any resistors
        res = Part.objects.filter(description__contains='resistor')
        for r in res:
            self.assertEqual(r.total_stock, 0)
            self.assertEqual(r.available_stock, 0)

    def test_barcode(self):
        barcode = self.R1.format_barcode()
        self.assertIn('InvenTree', barcode)
        self.assertIn(self.R1.name, barcode)

    def test_copy(self):

        self.R2.deepCopy(self.R1, image=True, bom=True)
