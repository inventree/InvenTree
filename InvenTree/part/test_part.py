# Tests for the Part model

from allauth.account.models import EmailAddress

from django.conf import settings

from django.test import TestCase
from django.core.exceptions import ValidationError

import os

from InvenTree.InvenTree.helpers import InvenTreeTestCate

from .models import Part, PartCategory, PartCategoryStar, PartStar, PartTestTemplate
from .models import rename_part_image
from .templatetags import inventree_extras

import part.settings

from InvenTree import version
from common.models import InvenTreeSetting, InvenTreeUserSetting, NotificationEntry, NotificationMessage
from common.notifications import storage, UIMessageNotification


class TemplateTagTest(InvenTreeTestCate):
    """ Tests for the custom template tag code """

    def test_define(self):
        self.assertEqual(int(inventree_extras.define(3)), 3)

    def test_str2bool(self):
        self.assertEqual(int(inventree_extras.str2bool('true')), True)
        self.assertEqual(int(inventree_extras.str2bool('yes')), True)
        self.assertEqual(int(inventree_extras.str2bool('none')), False)
        self.assertEqual(int(inventree_extras.str2bool('off')), False)

    def test_inrange(self):
        self.assertEqual(inventree_extras.inrange(3), range(3))

    def test_multiply(self):
        self.assertEqual(int(inventree_extras.multiply(3, 5)), 15)

    def test_add(self):
        self.assertEqual(int(inventree_extras.add(3, 5)), 8)

    def test_plugins_enabled(self):
        self.assertEqual(inventree_extras.plugins_enabled(), True)

    def test_inventree_instance_name(self):
        self.assertEqual(inventree_extras.inventree_instance_name(), 'InvenTree server')

    def test_inventree_base_url(self):
        self.assertEqual(inventree_extras.inventree_base_url(), '')

    def test_inventree_is_release(self):
        self.assertEqual(inventree_extras.inventree_is_release(), not version.isInvenTreeDevelopmentVersion())

    def test_inventree_docs_version(self):
        self.assertEqual(inventree_extras.inventree_docs_version(), version.inventreeDocsVersion())

    def test_hash(self):
        result_hash = inventree_extras.inventree_commit_hash()
        if settings.DOCKER:
            # Testing inside docker environment *may* return an empty git commit hash
            # In such a case, skip this check
            pass
        else:
            self.assertGreater(len(result_hash), 5)

    def test_date(self):
        d = inventree_extras.inventree_commit_date()
        if settings.DOCKER:
            # Testing inside docker environment *may* return an empty git commit hash
            # In such a case, skip this check
            pass
        else:
            self.assertEqual(len(d.split('-')), 3)

    def test_github(self):
        self.assertIn('github.com', inventree_extras.inventree_github_url())

    def test_docs(self):
        self.assertIn('inventree.readthedocs.io', inventree_extras.inventree_docs_url())

    def test_keyvalue(self):
        self.assertEqual(inventree_extras.keyvalue({'a': 'a'}, 'a'), 'a')

    def test_mail_configured(self):
        self.assertEqual(inventree_extras.mail_configured(), False)

    def test_user_settings(self):
        result = inventree_extras.user_settings(self.user)
        self.assertEqual(len(result), len(InvenTreeUserSetting.SETTINGS))

    def test_global_settings(self):
        result = inventree_extras.global_settings()
        self.assertEqual(len(result), len(InvenTreeSetting.SETTINGS))

    def test_visible_global_settings(self):
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
    """ Tests for the Part model """

    fixtures = [
        'category',
        'part',
        'location',
        'part_pricebreaks'
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

    def test_duplicate(self):
        """
        Test that we cannot create a "duplicate" Part
        """

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
        except:
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
        barcode = self.r1.format_barcode(brief=False)
        self.assertIn('InvenTree', barcode)
        self.assertIn(self.r1.name, barcode)

    def test_copy(self):
        self.r2.deep_copy(self.r1, image=True, bom=True)

    def test_sell_pricing(self):
        # check that the sell pricebreaks were loaded
        self.assertTrue(self.r1.has_price_breaks)
        self.assertEqual(self.r1.price_breaks.count(), 2)
        # check that the sell pricebreaks work
        self.assertEqual(float(self.r1.get_price(1)), 0.15)
        self.assertEqual(float(self.r1.get_price(10)), 1.0)

    def test_internal_pricing(self):
        # check that the sell pricebreaks were loaded
        self.assertTrue(self.r1.has_internal_price_breaks)
        self.assertEqual(self.r1.internal_price_breaks.count(), 2)
        # check that the sell pricebreaks work
        self.assertEqual(float(self.r1.get_internal_price(1)), 0.08)
        self.assertEqual(float(self.r1.get_internal_price(10)), 0.5)

    def test_metadata(self):
        """Unit tests for the Part metadata field"""

        p = Part.objects.get(pk=1)
        self.assertIsNone(p.metadata)

        self.assertIsNone(p.get_metadata('test'))
        self.assertEqual(p.get_metadata('test', backup_value=123), 123)

        # Test update via the set_metadata() method
        p.set_metadata('test', 3)
        self.assertEqual(p.get_metadata('test'), 3)

        for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
            p.set_metadata(k, k)

        self.assertEqual(len(p.metadata.keys()), 4)


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


class PartSettingsTest(InvenTreeTestCate):
    """
    Tests to ensure that the user-configurable default values work as expected.

    Some fields for the Part model can have default values specified by the user.
    """

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
        self.assertTrue(part.settings.part_purchaseable_default())
        self.assertFalse(part.settings.part_salable_default())
        self.assertFalse(part.settings.part_trackable_default())

    def test_initial(self):
        """
        Test the 'initial' default values (no default values have been set)
        """

        part = self.make_part()

        self.assertTrue(part.component)
        self.assertTrue(part.purchaseable)
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
        Part.objects.create(name='Hello', description='A thing', IPN='IPN123', revision='A')

        # Attempt to create a duplicate item (should fail)
        with self.assertRaises(ValidationError):
            part = Part(name='Hello', description='A thing', IPN='IPN123', revision='A')
            part.validate_unique()

        # Attempt to create item with duplicate IPN (should be allowed by default)
        Part.objects.create(name='Hello', description='A thing', IPN='IPN123', revision='B')

        # And attempt again with the same values (should fail)
        with self.assertRaises(ValidationError):
            part = Part(name='Hello', description='A thing', IPN='IPN123', revision='B')
            part.validate_unique()

        # Now update the settings so duplicate IPN values are *not* allowed
        InvenTreeSetting.set_setting('PART_ALLOW_DUPLICATE_IPN', False, self.user)

        with self.assertRaises(ValidationError):
            part = Part(name='Hello', description='A thing', IPN='IPN123', revision='C')
            part.full_clean()

        # Any duplicate IPN should raise an error
        Part.objects.create(name='xyz', revision='1', description='A part', IPN='UNIQUE')

        # Case insensitive, so variations on spelling should throw an error
        for ipn in ['UNiquE', 'uniQuE', 'unique']:
            with self.assertRaises(ValidationError):
                Part.objects.create(name='xyz', revision='2', description='A part', IPN=ipn)

        with self.assertRaises(ValidationError):
            Part.objects.create(name='zyx', description='A part', IPN='UNIQUE')

        # However, *blank* / empty IPN values should be allowed, even if duplicates are not
        # Note that leading / trailling whitespace characters are trimmed, too
        Part.objects.create(name='abc', revision='1', description='A part', IPN=None)
        Part.objects.create(name='abc', revision='2', description='A part', IPN='')
        Part.objects.create(name='abc', revision='3', description='A part', IPN=None)
        Part.objects.create(name='abc', revision='4', description='A part', IPN='  ')
        Part.objects.create(name='abc', revision='5', description='A part', IPN='  ')
        Part.objects.create(name='abc', revision='6', description='A part', IPN=' ')


class PartSubscriptionTests(InvenTreeTestCate):

    fixtures = [
        'location',
        'category',
        'part',
    ]

    def setUp(self):
        super().setUp()

        # electronics / IC / MCU
        self.category = PartCategory.objects.get(pk=4)

        self.part = Part.objects.create(
            category=self.category,
            name='STM32F103',
            description='Currently worth a lot of money',
            is_template=True,
        )

    def test_part_subcription(self):
        """
        Test basic subscription against a part
        """

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
        """
        Test subscription against a parent part
        """

        # Construct a sub-part to star against
        sub_part = Part.objects.create(
            name='sub_part',
            description='a sub part',
            variant_of=self.part,
        )

        self.assertFalse(sub_part.is_starred_by(self.user))

        # Subscribe to the "parent" part
        self.part.set_starred(self.user, True)

        self.assertTrue(self.part.is_starred_by(self.user))
        self.assertTrue(sub_part.is_starred_by(self.user))

    def test_category_subscription(self):
        """
        Test subscription against a PartCategory
        """

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
        """
        Check that a parent category can be subscribed to
        """

        # Top-level "electronics" category
        cat = PartCategory.objects.get(pk=1)

        cat.set_starred(self.user, True)

        # Check base category
        self.assertTrue(cat.is_starred_by(self.user))

        # Check lower level category
        self.assertTrue(self.category.is_starred_by(self.user))

        # Check part
        self.assertTrue(self.part.is_starred_by(self.user))


class BaseNotificationIntegrationTest(InvenTreeTestCate):
    """ Integration test for notifications """

    fixtures = [
        'location',
        'category',
        'part',
        'stock'
    ]

    def setUp(self):
        super().setUp()
        # Add Mailadress
        EmailAddress.objects.create(user=self.user, email='test@testing.com')

        # Define part that will be tested
        self.part = Part.objects.get(name='R_2K2_0805')

    def _notification_run(self, run_class=None):
        """
        Run a notification test suit through.
        If you only want to test one class pass it to run_class
        """
        # reload notification methods
        storage.collect(run_class)

        # There should be no notification runs
        self.assertEqual(NotificationEntry.objects.all().count(), 0)

        # Test that notifications run through without errors
        self.part.minimum_stock = self.part.get_stock_count() + 1  # make sure minimum is one higher than current count
        self.part.save()

        # There should be no notification as no-one is subscribed
        self.assertEqual(NotificationEntry.objects.all().count(), 0)

        # Subscribe and run again
        self.part.set_starred(self.user, True)
        self.part.save()

        # There should be 1 notification
        self.assertEqual(NotificationEntry.objects.all().count(), 1)


class PartNotificationTest(BaseNotificationIntegrationTest):
    """ Integration test for part notifications """

    def test_notification(self):
        self._notification_run(UIMessageNotification)

        # There should be 1 notification message right now
        self.assertEqual(NotificationMessage.objects.all().count(), 1)

        # Try again -> cover the already send line
        self.part.save()

        # There should not be more messages
        self.assertEqual(NotificationMessage.objects.all().count(), 1)
