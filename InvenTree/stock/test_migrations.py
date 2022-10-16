"""Unit tests for data migrations in the 'stock' app"""

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree import helpers


class TestSerialNumberMigration(MigratorTestCase):
    """Test data migration which updates serial numbers"""

    migrate_from = ('stock', '0067_alter_stockitem_part')
    migrate_to = ('stock', helpers.getNewestMigrationFile('stock'))

    def prepare(self):
        """Create initial data for this migration"""

        Part = self.old_state.apps.get_model('part', 'part')
        StockItem = self.old_state.apps.get_model('stock', 'stockitem')

        # Create a base part
        my_part = Part.objects.create(
            name='PART-123',
            description='Some part',
            active=True,
            trackable=True,
            level=0,
            tree_id=0,
            lft=0, rght=0
        )

        # Create some serialized stock items
        for sn in range(10, 20):
            StockItem.objects.create(
                part=my_part,
                quantity=1,
                serial=sn,
                level=0,
                tree_id=0,
                lft=0, rght=0
            )

        # Create a stock item with a very large serial number
        item = StockItem.objects.create(
            part=my_part,
            quantity=1,
            serial='9999999999999999999999999999999999999999999999999999999999999',
            level=0,
            tree_id=0,
            lft=0, rght=0
        )

        self.big_ref_pk = item.pk

    def test_migrations(self):
        """Test that the migrations have been applied correctly"""

        StockItem = self.new_state.apps.get_model('stock', 'stockitem')

        # Check that the serial number integer conversion has been applied correctly
        for sn in range(10, 20):
            item = StockItem.objects.get(serial_int=sn)

            self.assertEqual(item.serial, str(sn))

        big_ref_item = StockItem.objects.get(pk=self.big_ref_pk)

        # Check that the StockItem maximum serial number
        self.assertEqual(big_ref_item.serial, '9999999999999999999999999999999999999999999999999999999999999')
        self.assertEqual(big_ref_item.serial_int, 0x7fffffff)
