"""Data migration unit tests for the 'common' app."""

import io
import os

from django.core.files.base import ContentFile

from django_test_migrations.contrib.unittest_case import MigratorTestCase


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
