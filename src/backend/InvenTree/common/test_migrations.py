"""Data migration unit tests for the 'common' app."""

import io
import shutil
import tempfile

from django.core.files.base import ContentFile
from django.test import override_settings

from django_test_migrations.contrib.unittest_case import MigratorTestCase
from PIL import Image

from InvenTree import unit_test


def get_legacy_models():
    """Return a set of legacy attachment models."""
    # Legacy attachment types to convert:
    # app_label, table name, target model, model ref
    return [
        ('build', 'BuildOrderAttachment', 'build', 'build'),
        ('company', 'CompanyAttachment', 'company', 'company'),
        (
            'company',
            'ManufacturerPartAttachment',
            'manufacturerpart',
            'manufacturer_part',
        ),
        ('order', 'PurchaseOrderAttachment', 'purchaseorder', 'order'),
        ('order', 'SalesOrderAttachment', 'salesorder', 'order'),
        ('order', 'ReturnOrderAttachment', 'returnorder', 'order'),
        ('part', 'PartAttachment', 'part', 'part'),
        ('stock', 'StockItemAttachment', 'stockitem', 'stock_item'),
    ]


def generate_attachment():
    """Generate a file attachment object for test upload."""
    file_object = io.StringIO('Some dummy data')
    file_object.seek(0)

    return ContentFile(file_object.getvalue(), 'test.txt')


class TestLegacyAttachmentMigration(MigratorTestCase):
    """Test entire schema migration sequence for the common app."""

    migrate_from = ('common', '0024_notesimage_model_id_notesimage_model_type')
    migrate_to = ('common', unit_test.getNewestMigrationFile('common'))

    def prepare(self):
        """Create initial data.

        Legacy attachment model types are:
        - BuildOrderAttachment
        - CompanyAttachment
        - ManufacturerPartAttachment
        - PurchaseOrderAttachment
        - SalesOrderAttachment
        - ReturnOrderAttachment
        - PartAttachment
        - StockItemAttachment
        """
        # Dummy MPPT data
        tree = {'tree_id': 0, 'level': 0, 'lft': 0, 'rght': 0}

        # BuildOrderAttachment
        Part = self.old_state.apps.get_model('part', 'Part')
        Build = self.old_state.apps.get_model('build', 'Build')

        part = Part.objects.create(
            name='Test Part',
            description='Test Part Description',
            active=True,
            assembly=True,
            purchaseable=True,
            **tree,
        )

        build = Build.objects.create(part=part, title='Test Build', quantity=10, **tree)

        PartAttachment = self.old_state.apps.get_model('part', 'PartAttachment')
        PartAttachment.objects.create(
            part=part, attachment=generate_attachment(), comment='Test file attachment'
        )
        PartAttachment.objects.create(
            part=part, link='http://example.com', comment='Test link attachment'
        )
        self.assertEqual(PartAttachment.objects.count(), 2)

        BuildOrderAttachment = self.old_state.apps.get_model(
            'build', 'BuildOrderAttachment'
        )
        BuildOrderAttachment.objects.create(
            build=build, link='http://example.com', comment='Test comment'
        )
        BuildOrderAttachment.objects.create(
            build=build, attachment=generate_attachment(), comment='a test file'
        )
        self.assertEqual(BuildOrderAttachment.objects.count(), 2)

        StockItem = self.old_state.apps.get_model('stock', 'StockItem')
        StockItemAttachment = self.old_state.apps.get_model(
            'stock', 'StockItemAttachment'
        )

        item = StockItem.objects.create(part=part, quantity=10, **tree)

        StockItemAttachment.objects.create(
            stock_item=item,
            attachment=generate_attachment(),
            comment='Test file attachment',
        )
        StockItemAttachment.objects.create(
            stock_item=item, link='http://example.com', comment='Test link attachment'
        )
        self.assertEqual(StockItemAttachment.objects.count(), 2)

        Company = self.old_state.apps.get_model('company', 'Company')
        CompanyAttachment = self.old_state.apps.get_model(
            'company', 'CompanyAttachment'
        )

        company = Company.objects.create(
            name='Test Company',
            description='Test Company Description',
            is_customer=True,
            is_manufacturer=True,
            is_supplier=True,
        )

        CompanyAttachment.objects.create(
            company=company,
            attachment=generate_attachment(),
            comment='Test file attachment',
        )
        CompanyAttachment.objects.create(
            company=company, link='http://example.com', comment='Test link attachment'
        )
        self.assertEqual(CompanyAttachment.objects.count(), 2)

        PurchaseOrder = self.old_state.apps.get_model('order', 'PurchaseOrder')
        PurchaseOrderAttachment = self.old_state.apps.get_model(
            'order', 'PurchaseOrderAttachment'
        )

        po = PurchaseOrder.objects.create(
            reference='PO-12345',
            supplier=company,
            description='Test Purchase Order Description',
        )

        PurchaseOrderAttachment.objects.create(
            order=po, attachment=generate_attachment(), comment='Test file attachment'
        )
        PurchaseOrderAttachment.objects.create(
            order=po, link='http://example.com', comment='Test link attachment'
        )
        self.assertEqual(PurchaseOrderAttachment.objects.count(), 2)

        SalesOrder = self.old_state.apps.get_model('order', 'SalesOrder')
        SalesOrderAttachment = self.old_state.apps.get_model(
            'order', 'SalesOrderAttachment'
        )

        so = SalesOrder.objects.create(
            reference='SO-12345',
            customer=company,
            description='Test Sales Order Description',
        )

        SalesOrderAttachment.objects.create(
            order=so, attachment=generate_attachment(), comment='Test file attachment'
        )
        SalesOrderAttachment.objects.create(
            order=so, link='http://example.com', comment='Test link attachment'
        )
        self.assertEqual(SalesOrderAttachment.objects.count(), 2)

        ReturnOrder = self.old_state.apps.get_model('order', 'ReturnOrder')
        ReturnOrderAttachment = self.old_state.apps.get_model(
            'order', 'ReturnOrderAttachment'
        )

        ro = ReturnOrder.objects.create(
            reference='RO-12345',
            customer=company,
            description='Test Return Order Description',
        )

        ReturnOrderAttachment.objects.create(
            order=ro, attachment=generate_attachment(), comment='Test file attachment'
        )
        ReturnOrderAttachment.objects.create(
            order=ro, link='http://example.com', comment='Test link attachment'
        )
        self.assertEqual(ReturnOrderAttachment.objects.count(), 2)

    def test_items_exist(self):
        """Test to ensure that the attachments are correctly migrated."""
        Attachment = self.new_state.apps.get_model('common', 'Attachment')

        self.assertEqual(Attachment.objects.count(), 14)

        for model in [
            'build',
            'company',
            'purchaseorder',
            'returnorder',
            'salesorder',
            'part',
            'stockitem',
        ]:
            self.assertEqual(Attachment.objects.filter(model_type=model).count(), 2)


def generate_image(filename: str = 'test.png', fmt: str = 'PNG') -> ContentFile:
    """Generate a Django dummy image for test inventreeimage."""
    color = (255, 0, 0)

    img = Image.new(mode='RGB', size=(100, 100), color=color)

    buffer = io.BytesIO()
    img.save(buffer, format=fmt)
    buffer.seek(0)

    return ContentFile(buffer.read(), name=filename)


class TestLegacyImageMigration(MigratorTestCase):
    """Test that any Company.image and Part.image values are correctly migrated."""

    migrate_from = [('common', '0039_emailthread_emailmessage')]
    migrate_to = [('common', unit_test.getNewestMigrationFile('common'))]

    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        super().setUpClass()
        cls._temp_media = tempfile.mkdtemp(prefix='test_media_')
        cls._override = override_settings(MEDIA_ROOT=cls._temp_media)
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        """Clean up after the test class."""
        super().tearDownClass()
        cls._override.disable()
        shutil.rmtree(cls._temp_media, ignore_errors=True)

    def prepare(self):
        """Populate the 'old' database state (before the migration)."""
        # --- COMPANY SETUP ---
        Company = self.old_state.apps.get_model('company', 'company')
        self.initial_data = [
            {'name': 'CoOne', 'file_name': 'test01.png'},
            {'name': 'CoTwo', 'file_name': 'test02.png'},
        ]
        self.co_pks = []
        for entry in self.initial_data:
            co = Company.objects.create(
                name=entry['name'], image=generate_image(filename=entry['file_name'])
            )
            self.co_pks.append(co.pk)

        no_image_co = Company.objects.create(
            name='NoImageCo', description='No image here'
        )
        self.no_image_pk = no_image_co.pk

        # --- PART SETUP ---
        Part = self.old_state.apps.get_model('part', 'part')
        # Two parts sharing the same image filename (to test deduplication)

        # Dummy MPPT data
        tree = {'tree_id': 0, 'level': 0, 'lft': 0, 'rght': 0}

        self.part_initial_data = [
            {'name': 'PartOne', 'file_name': 'part01.png'},
            {'name': 'PartTwo', 'file_name': 'part01.png'},
        ]
        self.part_pks = []
        for entry in self.part_initial_data:
            part = Part.objects.create(
                name=entry['name'],
                description='Test Part Description',
                active=True,
                assembly=True,
                purchaseable=True,
                image=generate_image(filename=entry['file_name']),
                **tree,
            )
            self.part_pks.append(part.pk)

        # Part with no image
        no_image_part = Part.objects.create(
            name='NoImagePart',
            description='Test NoImagePart Description',
            active=True,
            assembly=True,
            purchaseable=True,
            **tree,
        )
        self.no_image_part_pk = no_image_part.pk

    def test_company_image_migrated(self):
        """After applying the migration, Company images should be migrated."""
        InvenTreeImage = self.new_state.apps.get_model('common', 'inventreeimage')
        ContentType = self.new_state.apps.get_model('contenttypes', 'contenttype')

        ct = ContentType.objects.get(app_label='company', model='company')

        # Exactly two images should have been created
        all_imgs = InvenTreeImage.objects.filter(content_type_id=ct.pk)
        self.assertEqual(all_imgs.count(), len(self.initial_data))

        # Check each migrated image
        for idx, _ in enumerate(self.initial_data):
            pk = self.co_pks[idx]
            inv_img = InvenTreeImage.objects.get(content_type_id=ct.pk, object_id=pk)
            self.assertTrue(
                inv_img.primary, f'Image for company {pk} not marked primary'
            )

        # Ensure no image was created for the company that had none
        with self.assertRaises(InvenTreeImage.DoesNotExist):
            InvenTreeImage.objects.get(
                content_type_id=ct.pk, object_id=self.no_image_pk
            )

    def test_part_image_migrated(self):
        """After applying the migration, Part images should be migrated and deduplicated."""
        InvenTreeImage = self.new_state.apps.get_model('common', 'inventreeimage')
        ContentType = self.new_state.apps.get_model('contenttypes', 'contenttype')

        ct_part = ContentType.objects.get(app_label='part', model='part')

        # Should have one InvenTreeImage per Part with an image
        part_imgs = InvenTreeImage.objects.filter(content_type_id=ct_part.pk)
        self.assertEqual(part_imgs.count(), len(self.part_initial_data))

        # Each part image must exist and be marked primary
        for pk in self.part_pks:
            img = InvenTreeImage.objects.get(content_type_id=ct_part.pk, object_id=pk)
            self.assertTrue(img.primary, f'Image for part {pk} not marked primary')

        # Deduplication: both entries should reference the _same_ stored filename
        stored_names = {img.image.name for img in part_imgs}
        self.assertEqual(len(stored_names), 1, 'Duplicate images were not deduplicated')

        # Ensure no image was created for the part that had none
        with self.assertRaises(InvenTreeImage.DoesNotExist):
            InvenTreeImage.objects.get(
                content_type_id=ct_part.pk, object_id=self.no_image_part_pk
            )
