from django.test import TestCase

from .models import Part


class BomItemTest(TestCase):

    fixtures = [
        'category',
        'part',
        'location',
        'bom',
    ]

    def setUp(self):
        self.bob = Part.objects.get(id=100)
        self.orphan = Part.objects.get(name='Orphan')

    def test_has_bom(self):
        self.assertFalse(self.orphan.has_bom)
        self.assertTrue(self.bob.has_bom)

        self.assertEqual(self.bob.bom_count, 4)

    def test_in_bom(self):
        parts = self.bob.required_parts()

        self.assertIn(self.orphan, parts)

    def test_bom_export(self):
        parts = self.bob.required_parts()

        data = self.bob.export_bom(format='csv')

        for p in parts:
            self.assertIn(p.name, data)
            self.assertIn(p.description, data)
