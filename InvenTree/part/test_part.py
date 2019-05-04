from django.test import TestCase

import os

from .models import Part
from .models import rename_part_image


class SimplePartTest(TestCase):
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
