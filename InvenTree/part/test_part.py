from django.test import TestCase

import os

from .models import Part, PartCategory
from .models import rename_part_image


class SimplePartTest(TestCase):

    def setUp(self):

        cat = PartCategory.objects.create(name='TLC', description='Top level category')

        self.px = Part.objects.create(name='x', description='A part called x', buildable=True)
        self.py = Part.objects.create(name='y', description='A part called y', consumable=False)
        self.pz = Part.objects.create(name='z', description='A part called z', category=cat)

    def test_metadata(self):
        self.assertEqual(self.px.name, 'x')
        self.assertEqual(self.py.get_absolute_url(), '/part/2/')
        self.assertEqual(str(self.pz), 'z - A part called z')

    def test_category(self):
        self.assertEqual(self.px.category_path, '')
        self.assertEqual(self.pz.category_path, 'TLC')

    def test_rename_img(self):
        img = rename_part_image(self.px, 'hello.png')
        self.assertEqual(img, os.path.join('part_images', 'part_1_img.png'))

        img = rename_part_image(self.pz, 'test')
        self.assertEqual(img, os.path.join('part_images', 'part_3_img'))

    def test_stock(self):
        # Stock should initially be zero
        self.assertEqual(self.px.total_stock, 0)
        self.assertEqual(self.py.available_stock, 0)