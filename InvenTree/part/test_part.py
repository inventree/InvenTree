# Tests for the Part model

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.auth import get_user_model

from django.test import TestCase
from django.core.exceptions import ValidationError

import os

from .models import Part, PartTestTemplate
from .models import rename_part_image, match_part_names
from .templatetags import inventree_extras

import part.settings

from common.models import InvenTreeSetting


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
        self.assertIn('inventree.readthedocs.io', inventree_extras.inventree_docs_url())


class PartTest(TestCase):
    """ Tests for the Part model """

    fixtures = [
        'category',
        'part',
        'location',
    ]

    def setUp(self):
        self.r1 = Part.objects.get(name='R_2K2_0805')
        self.r2 = Part.objects.get(name='R_4K7_0603')

        self.c1 = Part.objects.get(name='C_22N_0805')

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
        self.assertEqual(self.r1.name, 'R_2K2_0805')
        self.assertEqual(self.r1.get_absolute_url(), '/part/3/')

    def test_category(self):
        self.assertEqual(str(self.c1.category), 'Electronics/Capacitors - Capacitors')

        orphan = Part.objects.get(name='Orphan')
        self.assertIsNone(orphan.category)
        self.assertEqual(orphan.category_path, '')

    def test_rename_img(self):
        img = rename_part_image(self.r1, 'hello.png')
        self.assertEqual(img, os.path.join('part_images', 'hello.png'))
        
    def test_stock(self):
        # No stock of any resistors
        res = Part.objects.filter(description__contains='resistor')
        for r in res:
            self.assertEqual(r.total_stock, 0)
            self.assertEqual(r.available_stock, 0)

    def test_barcode(self):
        barcode = self.r1.format_barcode()
        self.assertIn('InvenTree', barcode)
        self.assertIn(self.r1.name, barcode)

    def test_copy(self):
        self.r2.deep_copy(self.r1, image=True, bom=True)

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


class PartSettingsTest(TestCase):
    """
    Tests to ensure that the user-configurable default values work as expected.

    Some fields for the Part model can have default values specified by the user.
    """
    
    def setUp(self):
        # Create a user for auth
        user = get_user_model()

        self.user = user.objects.create_user(
            username='testuser',
            email='test@testing.com',
            password='password',
            is_staff=True
        )

    def make_part(self):
        """
        Helper function to create a simple part
        """

        part = Part.objects.create(
            name='Test Part',
            description='I am but a humble test part',
            IPN='IPN-123',
        )

        return part

    def test_defaults(self):
        """
        Test that the default values for the part settings are correct
        """

        self.assertTrue(part.settings.part_component_default())
        self.assertFalse(part.settings.part_purchaseable_default())
        self.assertFalse(part.settings.part_salable_default())
        self.assertFalse(part.settings.part_trackable_default())

    def test_initial(self):
        """
        Test the 'initial' default values (no default values have been set)
        """

        part = self.make_part()

        self.assertTrue(part.component)
        self.assertFalse(part.purchaseable)
        self.assertFalse(part.salable)
        self.assertFalse(part.trackable)

    def test_custom(self):
        """
        Update some of the part values and re-test
        """

        for val in [True, False]:
            InvenTreeSetting.set_setting('PART_COMPONENT', val, self.user)
            InvenTreeSetting.set_setting('PART_PURCHASEABLE', val, self.user)
            InvenTreeSetting.set_setting('PART_SALABLE', val, self.user)
            InvenTreeSetting.set_setting('PART_TRACKABLE', val, self.user)
            InvenTreeSetting.set_setting('PART_ASSEMBLY', val, self.user)
            InvenTreeSetting.set_setting('PART_TEMPLATE', val, self.user)

            self.assertEqual(val, InvenTreeSetting.get_setting('PART_COMPONENT'))
            self.assertEqual(val, InvenTreeSetting.get_setting('PART_PURCHASEABLE'))
            self.assertEqual(val, InvenTreeSetting.get_setting('PART_SALABLE'))
            self.assertEqual(val, InvenTreeSetting.get_setting('PART_TRACKABLE'))

            part = self.make_part()

            self.assertEqual(part.component, val)
            self.assertEqual(part.purchaseable, val)
            self.assertEqual(part.salable, val)
            self.assertEqual(part.trackable, val)
            self.assertEqual(part.assembly, val)
            self.assertEqual(part.is_template, val)
    
            Part.objects.filter(pk=part.pk).delete()

    def test_duplicate_ipn(self):
        """
        Test the setting which controls duplicate IPN values
        """

        # Create a part
        Part.objects.create(name='Hello', description='A thing', IPN='IPN123')

        # Attempt to create a duplicate item (should fail)
        with self.assertRaises(ValidationError):
            Part.objects.create(name='Hello', description='A thing', IPN='IPN123')

        # Attempt to create item with duplicate IPN (should be allowed by default)
        Part.objects.create(name='Hello', description='A thing', IPN='IPN123', revision='B')

        # And attempt again with the same values (should fail)
        with self.assertRaises(ValidationError):
            Part.objects.create(name='Hello', description='A thing', IPN='IPN123', revision='B')

        # Now update the settings so duplicate IPN values are *not* allowed
        InvenTreeSetting.set_setting('PART_ALLOW_DUPLICATE_IPN', False, self.user)

        with self.assertRaises(ValidationError):
            Part.objects.create(name='Hello', description='A thing', IPN='IPN123', revision='C')
