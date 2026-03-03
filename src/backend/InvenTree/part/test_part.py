"""Tests for the Part model."""

import os

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase

import part.settings
from common.models import NotificationEntry, NotificationMessage
from common.settings import get_global_setting, set_global_setting
from InvenTree import version
from InvenTree.templatetags import inventree_extras
from InvenTree.unit_test import InvenTreeTestCase, addUserPermission

from .models import (
    Part,
    PartCategory,
    PartCategoryStar,
    PartRelated,
    PartStar,
    PartTestTemplate,
    rename_part_image,
)


class TemplateTagTest(InvenTreeTestCase):
    """Tests for the custom template tag code."""

    def test_define(self):
        """Test the 'define' template tag."""
        self.assertEqual(int(inventree_extras.define(3)), 3)

    def test_str2bool(self):
        """Various test for the str2bool template tag."""
        self.assertEqual(int(inventree_extras.str2bool('true')), True)
        self.assertEqual(int(inventree_extras.str2bool('yes')), True)
        self.assertEqual(int(inventree_extras.str2bool('none')), False)
        self.assertEqual(int(inventree_extras.str2bool('off')), False)

    def test_inventree_instance_name(self):
        """Test the 'instance name' setting."""
        self.assertEqual(inventree_extras.inventree_instance_name(), 'InvenTree')

    def test_inventree_title(self):
        """Test the 'inventree_title' setting."""
        self.assertEqual(inventree_extras.inventree_title(), 'InvenTree')

    def test_inventree_customize(self):
        """Test the 'inventree_customize' template tag."""
        self.assertEqual(inventree_extras.inventree_customize('abc'), '')

    def test_inventree_version(self):
        """Test the 'version' setting."""
        self.assertEqual(
            inventree_extras.inventree_version(), version.inventreeVersion()
        )
        self.assertNotEqual(
            inventree_extras.inventree_version(shortstring=True),
            version.inventreeVersion(),
        )

    def test_hash(self):
        """Test that the commit hash template tag returns correctly."""
        result_hash = inventree_extras.inventree_commit_hash()
        if settings.DOCKER:  # pragma: no cover
            # Testing inside docker environment *may* return an empty git commit hash
            # In such a case, skip this check
            pass
        else:
            self.assertGreater(len(result_hash), 5)

    def test_date(self):
        """Test that the commit date template tag returns correctly."""
        d = inventree_extras.inventree_commit_date()
        if settings.DOCKER:  # pragma: no cover
            # Testing inside docker environment *may* return an empty git commit hash
            # In such a case, skip this check
            pass
        else:
            self.assertEqual(len(d.split('-')), 3)

    def test_keyvalue(self):
        """Test keyvalue template tag."""
        self.assertEqual(inventree_extras.keyvalue({'a': 'a'}, 'a'), 'a')

    def test_to_list(self):
        """Test the 'to_list' template tag."""
        self.assertEqual(inventree_extras.to_list(1, 2, 3), (1, 2, 3))

    def test_render_date(self):
        """Test the 'render_date' template tag."""
        self.assertEqual(inventree_extras.render_date('2021-01-01'), '2021-01-01')

        self.assertEqual(inventree_extras.render_date(None), None)
        self.assertEqual(inventree_extras.render_date('  '), None)
        self.assertEqual(inventree_extras.render_date('aaaa'), None)
        self.assertEqual(inventree_extras.render_date(1234), 1234)

    def test_setting_object(self):
        """Test the 'setting_object' template tag."""
        # Normal
        self.assertEqual(
            inventree_extras.setting_object('PART_ALLOW_DUPLICATE_IPN').value, True
        )

        # User
        self.assertEqual(
            inventree_extras.setting_object(
                'PART_ALLOW_DUPLICATE_IPN', user=self.user
            ).value,
            '',
        )

        # Method
        self.assertEqual(
            inventree_extras.setting_object(
                'PART_ALLOW_DUPLICATE_IPN', method='abc', user=self.user
            ).value,
            '',
        )

    def test_settings_value(self):
        """Test the 'settings_value' template tag."""
        # Normal
        self.assertEqual(
            inventree_extras.settings_value('PART_ALLOW_DUPLICATE_IPN'), True
        )

        # User
        self.assertEqual(
            inventree_extras.settings_value('PART_ALLOW_DUPLICATE_IPN', user=self.user),
            '',
        )
        self.logout()
        self.assertEqual(
            inventree_extras.settings_value('PART_ALLOW_DUPLICATE_IPN', user=self.user),
            '',
        )


class PartTest(TestCase):
    """Tests for the Part model."""

    fixtures = ['category', 'part', 'location', 'part_pricebreaks']

    @classmethod
    def setUpTestData(cls):
        """Create some Part instances as part of init routine."""
        super().setUpTestData()

        cls.r1 = Part.objects.get(name='R_2K2_0805')
        cls.r2 = Part.objects.get(name='R_4K7_0603')
        cls.c1 = Part.objects.get(name='C_22N_0805')

    def test_barcode_mixin(self):
        """Test the barcode mixin functionality."""
        self.assertEqual(Part.barcode_model_type(), 'part')

        p = Part.objects.get(pk=1)
        barcode = p.format_barcode()
        self.assertEqual(barcode, 'INV-PA1')

    def test_str(self):
        """Test string representation of a Part."""
        p = Part.objects.get(pk=100)
        self.assertEqual(str(p), 'BOB | Bob | A2 - Can we build it? Yes we can!')

    def test_duplicate(self):
        """Test that we cannot create a "duplicate" Part."""
        n = Part.objects.count()

        cat = PartCategory.objects.get(pk=1)

        Part.objects.create(
            category=cat,
            name='part',
            description='description',
            IPN='IPN',
            revision='A',
        )

        self.assertEqual(Part.objects.count(), n + 1)

        part = Part(
            category=cat,
            name='part',
            description='description',
            IPN='IPN',
            revision='A',
        )

        with self.assertRaises(ValidationError):
            part.validate_unique()

        try:
            part.save()
            self.assertTrue(False)  # pragma: no cover
        except Exception:
            pass

        self.assertEqual(Part.objects.count(), n + 1)

        # But we should be able to create a part with a different revision
        part_2 = Part.objects.create(
            category=cat,
            name='part',
            description='description',
            IPN='IPN',
            revision='B',
        )

        self.assertEqual(Part.objects.count(), n + 2)

        # Now, check that we cannot *change* part_2 to conflict
        part_2.revision = 'A'

        with self.assertRaises(ValidationError):
            part_2.validate_unique()

    def test_attributes(self):
        """Test Part attributes."""
        self.assertEqual(self.r1.name, 'R_2K2_0805')
        self.assertEqual(self.r1.get_absolute_url(), '/web/part/3')

    def test_category(self):
        """Test PartCategory path."""
        self.c1.category.save()
        self.assertEqual(str(self.c1.category), 'Electronics/Capacitors - Capacitors')

        orphan = Part.objects.get(name='Orphan')
        self.assertIsNone(orphan.category)
        self.assertEqual(orphan.category_path, '')

    def test_rename_img(self):
        """Test that an image can be renamed."""
        img = rename_part_image(self.r1, 'hello.png')
        self.assertEqual(img, os.path.join('part_images', 'hello.png'))

    def test_stock(self):
        """Test case where there is zero stock."""
        res = Part.objects.filter(description__contains='resistor')
        for r in res:
            self.assertEqual(r.total_stock, 0)
            self.assertEqual(r.available_stock, 0)

    def test_barcode(self):
        """Test barcode format functionality."""
        barcode = self.r1.format_barcode()
        self.assertEqual('INV-PA3', barcode)

    def test_sell_pricing(self):
        """Check that the sell pricebreaks were loaded."""
        self.assertTrue(self.r1.has_price_breaks)
        self.assertEqual(self.r1.price_breaks.count(), 2)
        # check that the sell pricebreaks work
        self.assertEqual(float(self.r1.get_price(1)), 0.15)
        self.assertEqual(float(self.r1.get_price(10)), 1.0)

    def test_internal_pricing(self):
        """Check that the sell pricebreaks were loaded."""
        self.assertTrue(self.r1.has_internal_price_breaks)
        self.assertEqual(self.r1.internal_price_breaks.count(), 2)
        # check that the sell pricebreaks work
        self.assertEqual(float(self.r1.get_internal_price(1)), 0.08)
        self.assertEqual(float(self.r1.get_internal_price(10)), 0.5)

    def test_metadata(self):
        """Unit tests for the metadata field."""
        for model in [Part]:
            p = model.objects.first()

            self.assertIsNone(p.get_metadata('test'))
            self.assertEqual(p.get_metadata('test', backup_value=123), 123)

            # Test update via the set_metadata() method
            p.set_metadata('test', 3)
            self.assertEqual(p.get_metadata('test'), 3)

            for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
                p.set_metadata(k, k)

            self.assertEqual(len(p.metadata.keys()), 4)

    def test_related(self):
        """Unit tests for the PartRelated model."""
        # Create a part relationship
        # Count before creation
        countbefore = PartRelated.objects.count()
        PartRelated.objects.create(part_1=self.r1, part_2=self.r2)
        self.assertEqual(PartRelated.objects.count(), countbefore + 1)

        # Creating a duplicate part relationship should fail
        with self.assertRaises(ValidationError):
            PartRelated.objects.create(part_1=self.r1, part_2=self.r2)

        # Creating an 'inverse' duplicate relationship should also fail
        with self.assertRaises(ValidationError):
            PartRelated.objects.create(part_1=self.r2, part_2=self.r1)

        # Try to add a self-referential relationship
        with self.assertRaises(ValidationError):
            PartRelated.objects.create(part_1=self.r2, part_2=self.r2)

        # Test relation lookup for each part
        r1_relations = self.r1.get_related_parts()
        self.assertEqual(len(r1_relations), 1)
        self.assertIn(self.r2, r1_relations)

        r2_relations = self.r2.get_related_parts()
        self.assertEqual(len(r2_relations), 1)
        self.assertIn(self.r1, r2_relations)

        # Delete a part, ensure the relationship also gets deleted
        self.r1.active = False
        self.r1.save()
        self.r1.delete()

        self.assertEqual(PartRelated.objects.count(), countbefore)
        self.assertEqual(len(self.r2.get_related_parts()), 0)

        # Add multiple part relationships to self.r2
        for p in Part.objects.all().exclude(pk=self.r2.pk):
            PartRelated.objects.create(part_1=p, part_2=self.r2)

        n = Part.objects.count() - 1

        self.assertEqual(PartRelated.objects.count(), n + countbefore)
        self.assertEqual(len(self.r2.get_related_parts()), n)

        # Deleting r2 should remove *all* newly created relationships
        self.r2.active = False
        self.r2.save()
        self.r2.delete()
        self.assertEqual(PartRelated.objects.count(), countbefore)

    def test_delete(self):
        """Test delete operation for a Part instance."""
        part = Part.objects.first()

        for active, locked in [(True, True), (True, False), (False, True)]:
            # Cannot delete part if it is active or locked
            part.active = active
            part.locked = locked
            part.save()

            with self.assertRaises(ValidationError):
                part.delete()

        part.active = False
        part.locked = False

        part.delete()

    def test_revisions(self):
        """Test the 'revision' and 'revision_of' field."""
        template = Part.objects.create(
            name='Template part', description='A template part', is_template=True
        )

        # Create a new part
        part = Part.objects.create(
            name='Master Part',
            description='Master part (will have revisions)',
            variant_of=template,
        )

        self.assertEqual(part.revisions.count(), 0)

        # Try to set as revision of itself
        with self.assertRaises(ValidationError) as exc:
            part.revision_of = part
            part.save()

        self.assertIn('Part cannot be a revision of itself', str(exc.exception))

        part.refresh_from_db()

        rev_a = Part.objects.create(
            name='Master Part', description='Master part (revision A)'
        )

        with self.assertRaises(ValidationError) as exc:
            rev_a.revision_of = part
            rev_a.save()

        self.assertIn('Revision code must be specified', str(exc.exception))

        with self.assertRaises(ValidationError) as exc:
            rev_a.revision_of = template
            rev_a.revision = 'A'
            rev_a.save()

        self.assertIn('Cannot make a revision of a template part', str(exc.exception))

        with self.assertRaises(ValidationError) as exc:
            rev_a.revision_of = part
            rev_a.revision = 'A'
            rev_a.save()

        self.assertIn('Parent part must point to the same template', str(exc.exception))

        rev_a.variant_of = template
        rev_a.revision_of = part
        rev_a.revision = 'A'
        rev_a.save()

        self.assertEqual(part.revisions.count(), 1)

        rev_b = Part.objects.create(
            name='Master Part', description='Master part (revision B)'
        )

        with self.assertRaises(ValidationError) as exc:
            rev_b.revision_of = rev_a
            rev_b.revision = 'B'
            rev_b.save()

        self.assertIn(
            'Cannot make a revision of a part which is already a revision',
            str(exc.exception),
        )

        rev_b.variant_of = template
        rev_b.revision_of = part
        rev_b.revision = 'B'
        rev_b.save()

        self.assertEqual(part.revisions.count(), 2)


class VariantTreeTest(TestCase):
    """Unit test for the Part variant tree structure."""

    fixtures = ['category', 'part', 'location']

    @classmethod
    def setUpTestData(cls):
        """Rebuild Part tree before running tests."""
        super().setUpTestData()

    def test_tree(self):
        """Test tree structure for fixtured data."""
        chair = Part.objects.get(pk=10000)
        self.assertEqual(chair.get_children().count(), 3)
        self.assertEqual(chair.get_descendant_count(), 4)

        green = Part.objects.get(pk=10004)
        self.assertEqual(green.get_ancestors().count(), 2)
        self.assertEqual(green.get_root(), chair)
        self.assertEqual(green.get_family().count(), 3)
        self.assertEqual(Part.objects.filter(tree_id=chair.tree_id).count(), 5)

    def test_part_creation(self):
        """Test that parts are created with the correct tree structure."""
        part_1 = Part.objects.create(name='Part 1', description='Part 1 description')

        part_2 = Part.objects.create(name='Part 2', description='Part 2 description')

        # Check that both parts have been created with unique tree IDs
        self.assertNotEqual(part_1.tree_id, part_2.tree_id)

        for p in [part_1, part_2]:
            self.assertEqual(p.level, 0)
            self.assertEqual(p.lft, 1)
            self.assertEqual(p.rght, 2)
            self.assertIsNone(p.variant_of)

            self.assertEqual(Part.objects.filter(tree_id=p.tree_id).count(), 1)

    def test_complex_tree(self):
        """Test a complex part template/variant tree."""
        template = Part.objects.create(
            name='Top Level Template',
            description='A top-level template part',
            is_template=True,
        )

        # Create some variant parts
        for x in ['A', 'B', 'C']:
            variant = Part.objects.create(
                name=f'Variant {x}',
                description=f'Variant part {x}',
                variant_of=template,
                is_template=True,
            )

            for ii in range(1, 4):
                Part.objects.create(
                    name=f'Sub-Variant {x}-{ii}',
                    description=f'Sub-variant part {x}-{ii}',
                    variant_of=variant,
                )

        template.refresh_from_db()

        self.assertEqual(template.get_children().count(), 3)
        self.assertEqual(template.get_descendants(include_self=False).count(), 12)

        for variant in template.get_children():
            self.assertEqual(variant.variant_of, template)
            self.assertEqual(variant.get_ancestors().count(), 1)
            self.assertEqual(variant.get_descendants(include_self=False).count(), 3)

            for child in variant.get_children():
                self.assertEqual(child.variant_of, variant)
                self.assertEqual(child.get_ancestors().count(), 2)
                self.assertEqual(child.get_descendants(include_self=False).count(), 0)

        # Let's graft one variant onto another
        variant_a = Part.objects.get(name='Variant A')
        variant_b = Part.objects.get(name='Variant B')
        variant_c = Part.objects.get(name='Variant C')

        variant_a.variant_of = variant_b
        variant_a.save()

        template.refresh_from_db()
        self.assertEqual(template.get_children().count(), 2)

        variant_a.refresh_from_db()
        variant_b.refresh_from_db()

        self.assertEqual(variant_a.get_ancestors().count(), 2)
        self.assertEqual(variant_a.variant_of, variant_b)
        self.assertEqual(variant_b.get_children().count(), 4)

        for child in variant_a.get_children():
            self.assertEqual(child.variant_of, variant_a)
            self.assertEqual(child.tree_id, template.tree_id)
            self.assertEqual(child.get_ancestors().count(), 3)
            self.assertEqual(child.level, 3)
            self.assertGreater(child.lft, variant_a.lft)
            self.assertGreater(child.lft, template.lft)
            self.assertLess(child.rght, variant_a.rght)
            self.assertLess(child.rght, template.rght)
            self.assertLess(child.lft, child.rght)

        # Let's graft one variant to its own tree
        variant_c.variant_of = None
        variant_c.save()

        template.refresh_from_db()
        variant_a.refresh_from_db()
        variant_b.refresh_from_db()
        variant_c.refresh_from_db()

        # Check total descendent count
        self.assertEqual(template.get_descendant_count(), 8)
        self.assertEqual(variant_a.get_descendant_count(), 3)
        self.assertEqual(variant_b.get_descendant_count(), 7)
        self.assertEqual(variant_c.get_descendant_count(), 3)

        # Check tree ID values
        self.assertEqual(template.tree_id, variant_a.tree_id)
        self.assertEqual(template.tree_id, variant_b.tree_id)
        self.assertNotEqual(template.tree_id, variant_c.tree_id)

        for child in variant_a.get_children():
            # template -> variant_b -> variant_b -> child
            self.assertEqual(child.tree_id, template.tree_id)
            self.assertEqual(child.get_ancestors().count(), 3)
            self.assertLess(child.lft, child.rght)

        for child in variant_b.get_children():
            # template -> variant_b -> child
            self.assertEqual(child.tree_id, template.tree_id)
            self.assertEqual(child.get_ancestors().count(), 2)
            self.assertLess(child.lft, child.rght)

        for child in variant_c.get_children():
            # variant_c -> child
            self.assertEqual(child.tree_id, variant_c.tree_id)
            self.assertEqual(child.get_ancestors().count(), 1)
            self.assertLess(child.lft, child.rght)

        # Next, let's delete an entire variant - ensure that sub-variants are moved up
        b_childs = variant_b.get_children()

        with self.assertRaises(ValidationError):
            variant_b.delete()

        # Mark as inactive to allow deletion
        variant_b.active = False
        variant_b.save()
        variant_b.delete()

        template.refresh_from_db()
        variant_a.refresh_from_db()

        # Top-level template should have now 4 direct children:
        # - 3x children grafted from variant_a
        # - variant_a - previously child of variant a
        self.assertEqual(template.get_children().count(), 4)

        self.assertEqual(variant_a.get_children().count(), 3)
        self.assertEqual(variant_a.variant_of, template)

        for child in b_childs:
            child.refresh_from_db()
            self.assertEqual(child.variant_of, template)
            self.assertEqual(child.get_ancestors().count(), 1)
            self.assertEqual(child.level, 2)


class TestTemplateTest(TestCase):
    """Unit test for the TestTemplate class."""

    fixtures = ['category', 'part', 'location', 'test_templates']

    def test_template_count(self):
        """Tests for the test template functions."""
        chair = Part.objects.get(pk=10000)

        # Tests for the top-level chair object (nothing above it!)
        self.assertEqual(chair.test_templates.count(), 5)
        self.assertEqual(chair.getTestTemplates().count(), 5)
        self.assertEqual(chair.getTestTemplates(required=True).count(), 4)
        self.assertEqual(chair.getTestTemplates(required=False).count(), 1)

        # Test the lowest-level part which has more associated tests
        variant = Part.objects.get(pk=10004)

        self.assertEqual(variant.getTestTemplates().count(), 6)
        self.assertEqual(variant.getTestTemplates(include_parent=False).count(), 0)
        self.assertEqual(variant.getTestTemplates(required=True).count(), 5)

        # Test the 'enabled' status check
        self.assertEqual(variant.getTestTemplates(enabled=True).count(), 6)
        self.assertEqual(variant.getTestTemplates(enabled=False).count(), 0)

        template = variant.getTestTemplates().first()
        template.enabled = False
        template.save()

        self.assertEqual(variant.getTestTemplates(enabled=True).count(), 5)
        self.assertEqual(variant.getTestTemplates(enabled=False).count(), 1)

    def test_uniqueness(self):
        """Test names must be unique for this part and also parts above."""
        variant = Part.objects.get(pk=10004)

        with self.assertRaises(ValidationError):
            PartTestTemplate.objects.create(part=variant, test_name='Record weight')

        # Test that error is raised if we try to create a duplicate test name
        with self.assertRaises(ValidationError):
            PartTestTemplate.objects.create(
                part=variant, test_name='Check chair is green'
            )

        # Also should fail if we attempt to create a test that would generate the same key
        with self.assertRaises(ValidationError):
            template = PartTestTemplate.objects.create(
                part=variant, test_name='ReCoRD       weiGHT  '
            )

            template.clean()

        # But we should be able to create a new one!
        n = variant.getTestTemplates().count()

        template = PartTestTemplate.objects.create(
            part=variant, test_name='A Sample Test'
        )

        # Test key should have been saved
        self.assertEqual(template.key, 'asampletest')

        self.assertEqual(variant.getTestTemplates().count(), n + 1)

    def test_key_generation(self):
        """Test the key generation method."""
        variant = Part.objects.get(pk=10004)

        invalid_names = ['', '+', '+++++++', '   ', '<>$&&&']

        for name in invalid_names:
            template = PartTestTemplate(part=variant, test_name=name)
            with self.assertRaises(ValidationError):
                template.clean()

        valid_names = [
            'Собранный щит',
            '!! 123 Собранный щит <><><> $$$$$ !!!',
            '----hello world----',
            'Olá Mundo',
            '我不懂中文',
        ]

        for name in valid_names:
            template = PartTestTemplate(part=variant, test_name=name)
            template.clean()


class PartSettingsTest(InvenTreeTestCase):
    """Tests to ensure that the user-configurable default values work as expected.

    Some fields for the Part model can have default values specified by the user.
    """

    def make_part(self):
        """Helper function to create a simple part."""
        cache.clear()

        part = Part.objects.create(
            name='Test Part', description='I am but a humble test part', IPN='IPN-123'
        )

        return part

    def test_defaults(self):
        """Test that the default values for the part settings are correct."""
        cache.clear()

        self.assertTrue(part.settings.part_component_default())
        self.assertTrue(part.settings.part_purchaseable_default())
        self.assertFalse(part.settings.part_salable_default())
        self.assertFalse(part.settings.part_trackable_default())

    def test_initial(self):
        """Test the 'initial' default values (no default values have been set)."""
        cache.clear()

        part = self.make_part()

        self.assertTrue(part.component)
        self.assertTrue(part.purchaseable)
        self.assertFalse(part.salable)
        self.assertFalse(part.trackable)

    def test_custom(self):
        """Update some of the part values and re-test."""
        for val in [True, False]:
            set_global_setting('PART_COMPONENT', val, self.user)
            set_global_setting('PART_PURCHASEABLE', val, self.user)
            set_global_setting('PART_SALABLE', val, self.user)
            set_global_setting('PART_TRACKABLE', val, self.user)
            set_global_setting('PART_ASSEMBLY', val, self.user)
            set_global_setting('PART_TEMPLATE', val, self.user)

            self.assertEqual(val, get_global_setting('PART_COMPONENT'))
            self.assertEqual(val, get_global_setting('PART_PURCHASEABLE'))
            self.assertEqual(val, get_global_setting('PART_SALABLE'))
            self.assertEqual(val, get_global_setting('PART_TRACKABLE'))

            part = self.make_part()

            self.assertEqual(part.component, val)
            self.assertEqual(part.purchaseable, val)
            self.assertEqual(part.salable, val)
            self.assertEqual(part.trackable, val)
            self.assertEqual(part.assembly, val)
            self.assertEqual(part.is_template, val)

            Part.objects.filter(pk=part.pk).delete()

    def test_duplicate_ipn(self):
        """Test the setting which controls duplicate IPN values."""
        # Create a part
        Part.objects.create(
            name='Hello', description='A thing', IPN='IPN123', revision='A'
        )

        # Attempt to create a duplicate item (should fail)
        with self.assertRaises(ValidationError):
            part = Part(name='Hello', description='A thing', IPN='IPN123', revision='A')
            part.validate_unique()

        # Attempt to create item with duplicate IPN (should be allowed by default)
        Part.objects.create(
            name='Hello', description='A thing', IPN='IPN123', revision='B'
        )

        # And attempt again with the same values (should fail)
        with self.assertRaises(ValidationError):
            part = Part(name='Hello', description='A thing', IPN='IPN123', revision='B')
            part.validate_unique()

        # Now update the settings so duplicate IPN values are *not* allowed
        set_global_setting('PART_ALLOW_DUPLICATE_IPN', False, self.user)

        with self.assertRaises(ValidationError):
            part = Part(name='Hello', description='A thing', IPN='IPN123', revision='C')
            part.full_clean()

        # Any duplicate IPN should raise an error
        Part.objects.create(
            name='xyz', revision='1', description='A part', IPN='UNIQUE'
        )

        # Case insensitive, so variations on spelling should throw an error
        for ipn in ['UNiquE', 'uniQuE', 'unique']:
            with self.assertRaises(ValidationError):
                Part.objects.create(
                    name='xyz', revision='2', description='A part', IPN=ipn
                )

        with self.assertRaises(ValidationError):
            Part.objects.create(name='zyx', description='A part', IPN='UNIQUE')

        # However, *blank* / empty IPN values should be allowed, even if duplicates are not
        # Note that leading / trailing whitespace characters are trimmed, too
        Part.objects.create(name='abc', revision='1', description='A part', IPN=None)
        Part.objects.create(name='abc', revision='2', description='A part', IPN='')
        Part.objects.create(name='abc', revision='3', description='A part', IPN=None)
        Part.objects.create(name='abc', revision='4', description='A part', IPN='  ')
        Part.objects.create(name='abc', revision='5', description='A part', IPN='  ')
        Part.objects.create(name='abc', revision='6', description='A part', IPN=' ')


class PartSubscriptionTests(InvenTreeTestCase):
    """Unit tests for part 'subscription'."""

    fixtures = ['location', 'category', 'part']

    @classmethod
    def setUpTestData(cls):
        """Create category and part data as part of setup routine."""
        super().setUpTestData()

        # Electronics / IC / MCU
        cls.category = PartCategory.objects.get(pk=4)

        cls.part = Part.objects.create(
            category=cls.category,
            name='STM32F103',
            description='Currently worth a lot of money',
            is_template=True,
        )

    def test_part_subcription(self):
        """Test basic subscription against a part."""
        # First check that the user is *not* subscribed to the part
        self.assertFalse(self.part.is_starred_by(self.user))

        # Now, subscribe directly to the part
        self.part.set_starred(self.user, True)

        self.assertEqual(PartStar.objects.count(), 1)

        self.assertTrue(self.part.is_starred_by(self.user))

        # Now, unsubscribe
        self.part.set_starred(self.user, False)

        self.assertFalse(self.part.is_starred_by(self.user))

    def test_variant_subscription(self):
        """Test subscription against a parent part."""
        # Construct a sub-part to star against
        sub_part = Part.objects.create(
            name='sub_part', description='a sub part', variant_of=self.part
        )

        self.assertFalse(sub_part.is_starred_by(self.user))

        # Subscribe to the "parent" part
        self.part.set_starred(self.user, True)

        self.assertTrue(self.part.is_starred_by(self.user))
        self.assertTrue(sub_part.is_starred_by(self.user))

    def test_category_subscription(self):
        """Test subscription against a PartCategory."""
        self.assertEqual(PartCategoryStar.objects.count(), 0)

        self.assertFalse(self.part.is_starred_by(self.user))
        self.assertFalse(self.category.is_starred_by(self.user))

        # Subscribe to the direct parent category
        self.category.set_starred(self.user, True)

        self.assertEqual(PartStar.objects.count(), 0)
        self.assertEqual(PartCategoryStar.objects.count(), 1)

        self.assertTrue(self.category.is_starred_by(self.user))
        self.assertTrue(self.part.is_starred_by(self.user))

        # Check that the "parent" category is not starred
        self.assertFalse(self.category.parent.is_starred_by(self.user))

        # Un-subscribe
        self.category.set_starred(self.user, False)

        self.assertFalse(self.category.is_starred_by(self.user))
        self.assertFalse(self.part.is_starred_by(self.user))

    def test_parent_category_subscription(self):
        """Check that a parent category can be subscribed to."""
        # Top-level "electronics" category
        cat = PartCategory.objects.get(pk=1)

        cat.set_starred(self.user, True)

        # Check base category
        self.assertTrue(cat.is_starred_by(self.user))

        # Check lower level category
        self.assertTrue(self.category.is_starred_by(self.user))

        # Check part
        self.assertTrue(self.part.is_starred_by(self.user))


class PartNotificationTest(InvenTreeTestCase):
    """Integration test for part notifications."""

    fixtures = ['location', 'category', 'part', 'stock']

    def test_low_stock_notification(self):
        """Test that a low stocknotification is generated."""
        NotificationEntry.objects.all().delete()
        NotificationMessage.objects.all().delete()

        part = Part.objects.get(name='R_2K2_0805')

        part.minimum_stock = part.get_stock_count() + 1

        part.save()

        # There should be no notifications created yet,
        # as there are no "subscribed" users for this part
        self.assertEqual(NotificationEntry.objects.all().count(), 0)
        self.assertEqual(NotificationMessage.objects.all().count(), 0)

        # Subscribe the user to the part
        addUserPermission(self.user, 'part', 'part', 'view')
        self.user.is_active = True
        self.user.save()
        part.set_starred(self.user, True)
        part.save()

        # Check that a UI notification entry has been created
        self.assertGreaterEqual(NotificationEntry.objects.all().count(), 1)
        self.assertGreaterEqual(NotificationMessage.objects.all().count(), 1)

        # No errors were generated during notification process
        from error_report.models import Error

        self.assertEqual(Error.objects.count(), 0)


class PartStockHistoryTest(InvenTreeTestCase):
    """Test generation of stock history entries."""

    fixtures = ['category', 'part', 'location', 'stock']

    def test_stock_history(self):
        """Test that stock history entries are generated correctly."""
        from part.models import Part, PartStocktake
        from part.stocktake import perform_stocktake

        N_STOCKTAKE = PartStocktake.objects.count()

        # Cache the initial count of stocktake entries
        stock_history_entries = {
            part.pk: part.stocktakes.count() for part in Part.objects.all()
        }

        # Initially, run with stocktake functionality disabled
        set_global_setting('STOCKTAKE_ENABLE', False)

        perform_stocktake()

        # No change, as functionality is disabled
        self.assertEqual(PartStocktake.objects.count(), N_STOCKTAKE)

        for p in Part.objects.all():
            self.assertEqual(p.stocktakes.count(), stock_history_entries[p.pk])

        # Now enable stocktake functionality
        set_global_setting('STOCKTAKE_ENABLE', True)

        # Ensure that there is at least one inactive part
        p = Part.objects.first()
        p.active = False
        p.save()

        perform_stocktake()
        self.assertGreater(PartStocktake.objects.count(), N_STOCKTAKE)

        for p in Part.objects.all():
            if p.active:
                # Active parts should have stocktake entries created
                self.assertGreater(p.stocktakes.count(), stock_history_entries[p.pk])
            else:
                # Inactive parts should not have stocktake entries created
                self.assertEqual(p.stocktakes.count(), stock_history_entries[p.pk])

        # Now, run again - should not create any new entries
        N_STOCKTAKE = PartStocktake.objects.count()
        perform_stocktake()
        self.assertEqual(PartStocktake.objects.count(), N_STOCKTAKE)
