from django.test import TestCase

from .models import Part, PartCategory


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
