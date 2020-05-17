# Tests for the Part model

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.test import TestCase
from django.core.exceptions import ValidationError

import os

from .models import Part, PartTestTemplate
from .models import rename_part_image, match_part_names
from .templatetags import inventree_extras


class TemplateTagTest(TestCase):
    """ Tests for the custom template tag code """

    def test_multiply(self):
        self.assertEqual(int(inventree_extras.multiply(3, 5)), 15)

    def test_version(self):
        self.assertEqual(type(inventree_extras.inventree_version()), str)

    def test_hash(self):
        hash = inventree_extras.inventree_commit_hash()
        self.assertGreater(len(hash), 5)

    def test_date(self):
        d = inventree_extras.inventree_commit_date()
        self.assertEqual(len(d.split('-')), 3)

    def test_github(self):
        self.assertIn('github.com', inventree_extras.inventree_github_url())

    def test_docs(self):
        self.assertIn('inventree.github.io', inventree_extras.inventree_docs_url())


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

        Part.objects.rebuild()

    def test_tree(self):
        # Test that the part variant tree is working properly
        chair = Part.objects.get(pk=10000)
        self.assertEqual(chair.get_children().count(), 3)
        self.assertEqual(chair.get_descendant_count(), 4)

        green = Part.objects.get(pk=10004)
        self.assertEqual(green.get_ancestors().count(), 2)
        self.assertEqual(green.get_root(), chair)
        self.assertEqual(green.get_family().count(), 3)
        self.assertEqual(Part.objects.filter(tree_id=chair.tree_id).count(), 5)

    def test_str(self):
        p = Part.objects.get(pk=100)
        self.assertEqual(str(p), "BOB | Bob | A2 - Can we build it?")

    def test_metadata(self):
        self.assertEqual(self.R1.name, 'R_2K2_0805')
        self.assertEqual(self.R1.get_absolute_url(), '/part/3/')

    def test_category(self):
        self.assertEqual(str(self.C1.category), 'Electronics/Capacitors - Capacitors')

        orphan = Part.objects.get(name='Orphan')
        self.assertIsNone(orphan.category)
        self.assertEqual(orphan.category_path, '')

    def test_rename_img(self):
        img = rename_part_image(self.R1, 'hello.png')
        self.assertEqual(img, os.path.join('part_images', 'hello.png'))
        
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

    def test_match_names(self):

        matches = match_part_names('M2x5 LPHS')

        self.assertTrue(len(matches) > 0)


class TestTemplateTest(TestCase):

    fixtures = [
        'category',
        'part',
        'location',
        'test_templates',
    ]

    def test_template_count(self):

        chair = Part.objects.get(pk=10000)

        # Tests for the top-level chair object (nothing above it!)
        self.assertEqual(chair.test_templates.count(), 5)
        self.assertEqual(chair.getTestTemplates().count(), 5)
        self.assertEqual(chair.getTestTemplates(required=True).count(), 4)
        self.assertEqual(chair.getTestTemplates(required=False).count(), 1)

        # Test the lowest-level part which has more associated tests
        variant = Part.objects.get(pk=10004)

        self.assertEqual(variant.getTestTemplates().count(), 7)
        self.assertEqual(variant.getTestTemplates(include_parent=False).count(), 1)
        self.assertEqual(variant.getTestTemplates(required=True).count(), 5)

    def test_uniqueness(self):
        # Test names must be unique for this part and also parts above

        variant = Part.objects.get(pk=10004)

        with self.assertRaises(ValidationError):
            PartTestTemplate.objects.create(
                part=variant,
                test_name='Record weight'
            )

        with self.assertRaises(ValidationError):
            PartTestTemplate.objects.create(
                part=variant,
                test_name='Check that chair is especially green'
            )

        # Also should fail if we attempt to create a test that would generate the same key
        with self.assertRaises(ValidationError):
            PartTestTemplate.objects.create(
                part=variant,
                test_name='ReCoRD       weiGHT  '
            )

        # But we should be able to create a new one!
        n = variant.getTestTemplates().count()

        PartTestTemplate.objects.create(part=variant, test_name='A Sample Test')

        self.assertEqual(variant.getTestTemplates().count(), n + 1)
