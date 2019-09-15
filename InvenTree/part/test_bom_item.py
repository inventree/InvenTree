from django.test import TestCase
import django.core.exceptions as django_exceptions

from .models import Part, BomItem


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

    def test_str(self):
        b = BomItem.objects.get(id=1)
        self.assertEqual(str(b), '10 x M2x4 LPHS to make BOB | Bob | A2')

    def test_has_bom(self):
        self.assertFalse(self.orphan.has_bom)
        self.assertTrue(self.bob.has_bom)

        self.assertEqual(self.bob.bom_count, 4)

    def test_in_bom(self):
        parts = self.bob.required_parts()

        self.assertIn(self.orphan, parts)

    def test_used_in(self):
        self.assertEqual(self.bob.used_in_count, 0)
        self.assertEqual(self.orphan.used_in_count, 1)

    def test_self_reference(self):
        """ Test that we get an appropriate error when we create a BomItem which points to itself """

        with self.assertRaises(django_exceptions.ValidationError):
            # A validation error should be raised here
            item = BomItem.objects.create(part=self.bob, sub_part=self.bob, quantity=7)
            item.clean()
