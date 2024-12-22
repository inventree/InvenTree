"""Tests for the Part model."""

import os

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.utils import override_settings

from allauth.account.models import EmailAddress

import part.settings
from common.models import (
    InvenTreeSetting,
    InvenTreeUserSetting,
    NotificationEntry,
    NotificationMessage,
)
from common.notifications import UIMessageNotification, storage
from common.settings import get_global_setting, set_global_setting
from InvenTree import version
from InvenTree.templatetags import inventree_extras
from InvenTree.unit_test import InvenTreeTestCase

from .models import (
    Part,
    PartCategory,
    PartCategoryStar,
    PartRelated,
    PartStar,
    PartStocktake,
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

    def test_add(self):
        """Test that the 'add."""
        self.assertEqual(int(inventree_extras.add(3, 5)), 8)

    def test_plugins_enabled(self):
        """Test the plugins_enabled tag."""
        self.assertEqual(inventree_extras.plugins_enabled(), True)

    def test_plugins_install_disabled(self):
        """Test the plugins_install_disabled tag."""
        self.assertEqual(inventree_extras.plugins_install_disabled(), False)

    def test_inventree_instance_name(self):
        """Test the 'instance name' setting."""
        self.assertEqual(inventree_extras.inventree_instance_name(), 'InvenTree')

    @override_settings(SITE_URL=None)
    def test_inventree_base_url(self):
        """Test that the base URL tag returns correctly."""
        self.assertEqual(inventree_extras.inventree_base_url(), '')

    def test_inventree_is_release(self):
        """Test that the release version check functions as expected."""
        self.assertEqual(
            inventree_extras.inventree_is_release(),
            not version.isInvenTreeDevelopmentVersion(),
        )

    def test_inventree_docs_version(self):
        """Test that the documentation version template tag returns correctly."""
        self.assertEqual(
            inventree_extras.inventree_docs_version(), version.inventreeDocsVersion()
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

    def test_github(self):
        """Test that the github URL template tag returns correctly."""
        self.assertIn('github.com', inventree_extras.inventree_github_url())

    def test_docs(self):
        """Test that the documentation URL template tag returns correctly."""
        self.assertIn('docs.inventree.org', inventree_extras.inventree_docs_url())

    def test_keyvalue(self):
        """Test keyvalue template tag."""
        self.assertEqual(inventree_extras.keyvalue({'a': 'a'}, 'a'), 'a')

    def test_mail_configured(self):
        """Test that mail configuration returns False."""
        self.assertEqual(inventree_extras.mail_configured(), False)

    def test_user_settings(self):
        """Test user settings."""
        result = inventree_extras.user_settings(self.user)
        self.assertEqual(len(result), len(InvenTreeUserSetting.SETTINGS))

    def test_global_settings(self):
        """Test global settings."""
        result = inventree_extras.global_settings()
        self.assertEqual(len(result), len(InvenTreeSetting.SETTINGS))

    def test_visible_global_settings(self):
        """Test that hidden global settings are actually hidden."""
        result = inventree_extras.visible_global_settings()

        n = len(result)

        n_hidden = 0
        n_visible = 0

        for val in InvenTreeSetting.SETTINGS.values():
            if val.get('hidden', False):
                n_hidden += 1
            else:
                n_visible += 1

        self.assertEqual(n, n_visible)


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

        Part.objects.rebuild()

    def test_barcode_mixin(self):
        """Test the barcode mixin functionality."""
        self.assertEqual(Part.barcode_model_type(), 'part')

        p = Part.objects.get(pk=1)
        barcode = p.format_barcode()
        self.assertEqual(barcode, '{"part": 1}')

    def test_tree(self):
        """Test that the part variant tree is working properly."""
        chair = Part.objects.get(pk=10000)
        self.assertEqual(chair.get_children().count(), 3)
        self.assertEqual(chair.get_descendant_count(), 4)

        green = Part.objects.get(pk=10004)
        self.assertEqual(green.get_ancestors().count(), 2)
        self.assertEqual(green.get_root(), chair)
        self.assertEqual(green.get_family().count(), 3)
        self.assertEqual(Part.objects.filter(tree_id=chair.tree_id).count(), 5)

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
        self.assertEqual(self.r1.get_absolute_url(), '/platform/part/3')

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
        self.assertEqual('{"part": 3}', barcode)

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

    def test_stocktake(self):
        """Test for adding stocktake data."""
        # Grab a part
        p = Part.objects.all().first()

        self.assertIsNone(p.last_stocktake)

        ps = PartStocktake.objects.create(part=p, quantity=100)

        self.assertIsNotNone(p.last_stocktake)
        self.assertEqual(p.last_stocktake, ps.date)

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
            print('rev a:', rev_a.revision_of, part.revision_of)
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


class BaseNotificationIntegrationTest(InvenTreeTestCase):
    """Integration test for notifications."""

    fixtures = ['location', 'category', 'part', 'stock']

    @classmethod
    def setUpTestData(cls):
        """Add an email address as part of initialization."""
        super().setUpTestData()

        # Add email address
        EmailAddress.objects.create(user=cls.user, email='test@testing.com')

        # Define part that will be tested
        cls.part = Part.objects.get(name='R_2K2_0805')

    def _notification_run(self, run_class=None):
        """Run a notification test suit through.

        If you only want to test one class pass it to run_class
        """
        # reload notification methods
        storage.collect(run_class)

        NotificationEntry.objects.all().delete()

        # There should be no notification runs
        self.assertEqual(NotificationEntry.objects.all().count(), 0)

        # Test that notifications run through without errors
        self.part.minimum_stock = (
            self.part.get_stock_count() + 1
        )  # make sure minimum is one higher than current count
        self.part.save()

        # There should be no notification as no-one is subscribed
        self.assertEqual(NotificationEntry.objects.all().count(), 0)

        # Subscribe and run again
        self.part.set_starred(self.user, True)
        self.part.save()

        # There should be 1 (or 2) notifications - in some cases an error is generated, which creates a subsequent notification
        self.assertIn(NotificationEntry.objects.all().count(), [1, 2])


class PartNotificationTest(BaseNotificationIntegrationTest):
    """Integration test for part notifications."""

    def test_notification(self):
        """Test that a notification is generated."""
        self._notification_run(UIMessageNotification)

        # There should be 1 notification message right now
        self.assertEqual(NotificationMessage.objects.all().count(), 1)

        # Try again -> cover the already send line
        self.part.save()

        # There should not be more messages
        self.assertEqual(NotificationMessage.objects.all().count(), 1)
