"""Data migration unit tests for the 'common' app."""

import io
import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from django_test_migrations.contrib.unittest_case import MigratorTestCase
from PIL import Image


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


class TestForwardMigrations(MigratorTestCase):
    """Test entire schema migration sequence for the common app."""

    migrate_from = ('common', '0024_notesimage_model_id_notesimage_model_type')
    migrate_to = ('common', '0039_emailthread_emailmessage')

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


class TestAttachmentThumbnailMigration(MigratorTestCase):
    """Test that migration 0043 correctly populates is_image and generates thumbnails for existing attachments."""

    migrate_from = ('common', '0041_auto_20251203_1244')
    migrate_to = ('common', '0043_auto_20260518_1206')

    def prepare(self):
        """Create a set of attachments with different file types in the pre-migration state.

        At this point the Attachment model has no is_image or thumbnail fields yet.
        Files are written to storage directly through the FileField so that the
        data migration can find them at their stored paths.
        """
        Attachment = self.old_state.apps.get_model('common', 'Attachment')

        # 1. Valid PNG image — migration should set is_image=True and create a thumbnail
        buf = io.BytesIO()
        Image.new('RGB', (100, 100), color='blue').save(buf, format='PNG')
        Attachment.objects.create(
            model_type='part',
            model_id=1,
            attachment=ContentFile(buf.getvalue(), name='valid_image.png'),
            comment='valid_image',
        )

        # 2. File with a .png extension but non-image content — migration should leave is_image=False
        Attachment.objects.create(
            model_type='part',
            model_id=1,
            attachment=ContentFile(b'this is not image data', name='corrupt.png'),
            comment='corrupt_image',
        )

        # 3. Plain text file — migration should leave is_image=False with no thumbnail
        Attachment.objects.create(
            model_type='part',
            model_id=1,
            attachment=ContentFile(b'Hello, InvenTree!', name='document.txt'),
            comment='text_file',
        )

        # 4. Link attachment (no file at all) — migration should skip it entirely
        Attachment.objects.create(
            model_type='part',
            model_id=1,
            link='https://example.com/resource',
            comment='link_attachment',
        )

        self.assertEqual(Attachment.objects.count(), 4)

    def test_attachment_thumbnails_after_migration(self):
        """After applying migrations 0042 and 0043, verify is_image and thumbnail are correct."""
        Attachment = self.new_state.apps.get_model('common', 'Attachment')

        self.assertEqual(Attachment.objects.count(), 4)

        # Valid image → is_image set, thumbnail file created in storage
        att = Attachment.objects.get(comment='valid_image')
        self.assertTrue(att.is_image)
        self.assertTrue(att.thumbnail)
        self.assertTrue(default_storage.exists(att.thumbnail.name))

        # Corrupt image → is_image not set, no thumbnail
        att = Attachment.objects.get(comment='corrupt_image')
        self.assertFalse(att.is_image)
        self.assertFalse(att.thumbnail)

        # Text file → is_image not set, no thumbnail
        att = Attachment.objects.get(comment='text_file')
        self.assertFalse(att.is_image)
        self.assertFalse(att.thumbnail)

        # Link attachment → is_image not set, no thumbnail
        att = Attachment.objects.get(comment='link_attachment')
        self.assertFalse(att.is_image)
        self.assertFalse(att.thumbnail)


class TestNoteMigrations(MigratorTestCase):
    """Test data migration of legacy 'notes' fields to the new Note model.

    - Migration common.0050 copies existing 'notes' field data into the Note model,
      converting the markdown content to HTML, and links any associated NotesImage objects.
    - Migration common.0051 removes the legacy 'model_type' and 'model_id' fields from NotesImage.
    """

    # Note: these targets must match the dependencies of the data migration (common.0050),
    # to ensure that the migration plan is truncated *before* the data migration is applied
    migrate_from = [
        ('common', '0049_note'),
        ('build', '0059_build_tags'),
        ('company', '0080_company_tags'),
        ('order', '0121_add_line_item_discount'),
        ('part', '0152_alter_partpricing_currency'),
        ('stock', '0125_remove_mptt_fields'),
    ]
    migrate_to = ('common', '0051_remove_notesimage_model_id_and_more')

    def generate_image(self, name: str):
        """Generate a dummy image file for upload."""
        buf = io.BytesIO()
        Image.new('RGB', (64, 64), color='red').save(buf, format='PNG')
        return ContentFile(buf.getvalue(), name=name)

    def get_model(self, app: str, model: str):
        """Fetch a historical model, working around the duplicate-column ORM bug.

        Historical models with a custom status field enumerate 'status_custom_key' twice
        (once from contribute_to_class on the status field, once from the explicit
        AddField migration), so ORM-generated INSERTs fail with
        'column specified more than once'. Remove the duplicated field entries here.
        """
        model_class = self.old_state.apps.get_model(app, model)

        seen = set()

        for field in list(model_class._meta.local_fields):
            if field.name in seen:
                model_class._meta.local_fields.remove(field)
            else:
                seen.add(field.name)

        model_class._meta._expire_cache()

        return model_class

    def prepare(self):
        """Create instances of each model type which supports notes."""
        # Dummy MPPT data
        tree = {'tree_id': 0, 'level': 0, 'lft': 0, 'rght': 0}

        NotesImage = self.get_model('common', 'NotesImage')

        Part = self.get_model('part', 'Part')
        Build = self.get_model('build', 'Build')
        StockItem = self.get_model('stock', 'StockItem')
        Company = self.get_model('company', 'Company')
        ManufacturerPart = self.get_model('company', 'ManufacturerPart')
        SupplierPart = self.get_model('company', 'SupplierPart')
        PurchaseOrder = self.get_model('order', 'PurchaseOrder')
        SalesOrder = self.get_model('order', 'SalesOrder')
        ReturnOrder = self.get_model('order', 'ReturnOrder')
        SalesOrderShipment = self.get_model('order', 'SalesOrderShipment')
        TransferOrder = self.get_model('order', 'TransferOrder')

        # An image which is not linked to any model, but is embedded in the notes markdown
        embedded_image = NotesImage.objects.create(
            image=self.generate_image('embedded.png')
        )

        # An image which is not linked to any model, and not referenced anywhere
        NotesImage.objects.create(image=self.generate_image('orphan.png'))

        part = Part.objects.create(
            name='Test Part',
            description='Test Part Description',
            active=True,
            assembly=True,
            purchaseable=True,
            notes=f'Some **bold** part notes\n\n![image]({embedded_image.image.url})',
            **tree,
        )

        # Parts with empty notes should not generate a Note entry
        Part.objects.create(
            name='Part with empty notes', description='x', notes='', **tree
        )
        Part.objects.create(
            name='Part with null notes', description='x', notes=None, **tree
        )

        # An image which is directly linked to the part instance
        NotesImage.objects.create(
            image=self.generate_image('linked.png'), model_type='part', model_id=part.pk
        )

        company = Company.objects.create(
            name='Test Company',
            description='Test Company Description',
            is_customer=True,
            is_manufacturer=True,
            is_supplier=True,
            notes='Some **bold** company notes',
        )

        so = SalesOrder.objects.create(
            reference='SO-12345',
            customer=company,
            description='Test Sales Order Description',
            notes='Some **bold** sales order notes',
        )

        instances = [
            ('part', part),
            ('company', company),
            ('salesorder', so),
            (
                'manufacturerpart',
                ManufacturerPart.objects.create(
                    part=part,
                    manufacturer=company,
                    MPN='MPN-123',
                    notes='Some **bold** manufacturer part notes',
                ),
            ),
            (
                'supplierpart',
                SupplierPart.objects.create(
                    part=part,
                    supplier=company,
                    SKU='SKU-123',
                    notes='Some **bold** supplier part notes',
                ),
            ),
            (
                'build',
                Build.objects.create(
                    part=part,
                    reference='BO-0001',
                    title='Test Build',
                    quantity=10,
                    notes='Some **bold** build notes',
                    **tree,
                ),
            ),
            (
                'stockitem',
                StockItem.objects.create(
                    part=part, quantity=10, notes='Some **bold** stock item notes'
                ),
            ),
            (
                'purchaseorder',
                PurchaseOrder.objects.create(
                    reference='PO-12345',
                    supplier=company,
                    description='Test Purchase Order Description',
                    notes='Some **bold** purchase order notes',
                ),
            ),
            (
                'returnorder',
                ReturnOrder.objects.create(
                    reference='RO-12345',
                    customer=company,
                    description='Test Return Order Description',
                    notes='Some **bold** return order notes',
                ),
            ),
            (
                'salesordershipment',
                SalesOrderShipment.objects.create(
                    order=so, reference='SHIP-001', notes='Some **bold** shipment notes'
                ),
            ),
            (
                'transferorder',
                TransferOrder.objects.create(
                    reference='TO-12345',
                    description='Test Transfer Order Description',
                    notes='Some **bold** transfer order notes',
                ),
            ),
        ]

        # Record the expected (model_type, model_id) values for later comparison
        self.expected_notes = [(model, instance.pk) for model, instance in instances]
        self.part_pk = part.pk

    def test_notes_migrated(self):
        """Test that a Note object has been created for each legacy notes field."""
        Note = self.new_state.apps.get_model('common', 'Note')
        ContentType = self.new_state.apps.get_model('contenttypes', 'ContentType')

        # One note per instance with non-empty notes (and no extras)
        self.assertEqual(Note.objects.count(), len(self.expected_notes))

        for model, pk in self.expected_notes:
            content_type = ContentType.objects.get(model=model)
            note = Note.objects.get(model_type=content_type, model_id=pk)

            self.assertEqual(note.title, 'Note')
            self.assertTrue(note.primary)
            self.assertFalse(note.template)

            # Markdown content has been converted to HTML
            self.assertIn('<strong>bold</strong>', note.content)
            self.assertNotIn('**', note.content)

    def test_images_migrated(self):
        """Test that NotesImage objects are correctly linked or removed."""
        Note = self.new_state.apps.get_model('common', 'Note')
        ContentType = self.new_state.apps.get_model('contenttypes', 'ContentType')
        NotesImage = self.new_state.apps.get_model('common', 'NotesImage')

        # The orphaned image has been removed
        self.assertEqual(NotesImage.objects.count(), 2)

        content_type = ContentType.objects.get(model='part')
        note = Note.objects.get(model_type=content_type, model_id=self.part_pk)

        # Both the directly linked image and the embedded image point to the part note
        for image in NotesImage.objects.all():
            self.assertEqual(image.note.pk, note.pk)


def prep_currency_migration(self, vals: str):
    """Prepare the environment for the currency migration tests."""
    # Set keys
    os.environ['INVENTREE_CURRENCIES'] = vals

    # And setting
    InvenTreeSetting = self.old_state.apps.get_model('common', 'InvenTreeSetting')

    setting = InvenTreeSetting(key='CURRENCY_CODES', value='123')
    setting.save()


class TestCurrencyMigration(MigratorTestCase):
    """Test currency migration."""

    migrate_from = ('common', '0022_projectcode_responsible')
    migrate_to = ('common', '0023_auto_20240602_1332')

    def prepare(self):
        """Prepare the environment for the migration test."""
        prep_currency_migration(self, 'USD,EUR,GBP')

    def test_currency_migration(self):
        """Test that the currency migration works."""
        InvenTreeSetting = self.old_state.apps.get_model('common', 'InvenTreeSetting')
        setting = InvenTreeSetting.objects.filter(key='CURRENCY_CODES').first()

        codes = str(setting.value).split(',')

        self.assertEqual(len(codes), 3)

        for code in ['USD', 'EUR', 'GBP']:
            self.assertIn(code, codes)


class TestCurrencyMigrationNo(MigratorTestCase):
    """Test currency migration."""

    migrate_from = ('common', '0022_projectcode_responsible')
    migrate_to = ('common', '0023_auto_20240602_1332')

    def prepare(self):
        """Prepare the environment for the migration test."""
        prep_currency_migration(self, 'YYY,ZZZ')

    def test_currency_migration(self):
        """Test that no currency migration occurs if wrong currencies are set."""
        InvenTreeSetting = self.old_state.apps.get_model('common', 'InvenTreeSetting')
        setting = InvenTreeSetting.objects.filter(key='CURRENCY_CODES').first()
        self.assertEqual(setting.value, '123')
