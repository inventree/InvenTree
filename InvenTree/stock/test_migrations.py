"""Unit tests for data migrations in the 'stock' app."""

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree import unit_test


class TestSerialNumberMigration(MigratorTestCase):
    """Test data migration which updates serial numbers."""

    migrate_from = ('stock', '0067_alter_stockitem_part')
    migrate_to = ('stock', unit_test.getNewestMigrationFile('stock'))

    def prepare(self):
        """Create initial data for this migration."""
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
            lft=0,
            rght=0,
        )

        # Create some serialized stock items
        for sn in range(10, 20):
            StockItem.objects.create(
                part=my_part, quantity=1, serial=sn, level=0, tree_id=0, lft=0, rght=0
            )

        # Create a stock item with a very large serial number
        item = StockItem.objects.create(
            part=my_part,
            quantity=1,
            serial='9999999999999999999999999999999999999999999999999999999999999',
            level=0,
            tree_id=0,
            lft=0,
            rght=0,
        )

        self.big_ref_pk = item.pk

    def test_migrations(self):
        """Test that the migrations have been applied correctly."""
        StockItem = self.new_state.apps.get_model('stock', 'stockitem')

        # Check that the serial number integer conversion has been applied correctly
        for sn in range(10, 20):
            item = StockItem.objects.get(serial_int=sn)

            self.assertEqual(item.serial, str(sn))

        big_ref_item = StockItem.objects.get(pk=self.big_ref_pk)

        # Check that the StockItem maximum serial number
        self.assertEqual(
            big_ref_item.serial,
            '9999999999999999999999999999999999999999999999999999999999999',
        )
        self.assertEqual(big_ref_item.serial_int, 0x7FFFFFFF)


class TestScheduledForDeletionMigration(MigratorTestCase):
    """Test data migration for removing 'scheduled_for_deletion' field."""

    migrate_from = ('stock', '0066_stockitem_scheduled_for_deletion')
    migrate_to = ('stock', unit_test.getNewestMigrationFile('stock'))

    def prepare(self):
        """Create some initial stock items."""
        Part = self.old_state.apps.get_model('part', 'part')
        StockItem = self.old_state.apps.get_model('stock', 'stockitem')

        for idx in range(5):
            part = Part.objects.create(
                name=f'Part_{idx}',
                description='Just a part, nothing to see here',
                active=True,
                level=0,
                tree_id=0,
                lft=0,
                rght=0,
            )

            for jj in range(5):
                StockItem.objects.create(
                    part=part,
                    quantity=jj + 5,
                    level=0,
                    tree_id=0,
                    lft=0,
                    rght=0,
                    scheduled_for_deletion=True,
                )

        # For extra points, create some parent-child relationships between stock items
        part = Part.objects.first()

        item_1 = StockItem.objects.create(
            part=part,
            quantity=100,
            level=0,
            tree_id=0,
            lft=0,
            rght=0,
            scheduled_for_deletion=True,
        )

        for _ in range(3):
            StockItem.objects.create(
                part=part,
                quantity=200,
                level=0,
                tree_id=0,
                lft=0,
                rght=0,
                scheduled_for_deletion=False,
                parent=item_1,
            )

        self.assertEqual(StockItem.objects.count(), 29)

    def test_migration(self):
        """Test that all stock items were actually removed."""
        StockItem = self.new_state.apps.get_model('stock', 'stockitem')

        # All the "scheduled for deletion" items have been removed
        self.assertEqual(StockItem.objects.count(), 3)


class TestTestResultMigration(MigratorTestCase):
    """Unit tests for StockItemTestResult data migrations."""

    migrate_from = ('stock', '0103_stock_location_types')
    migrate_to = ('stock', '0107_remove_stockitemtestresult_test_and_more')

    test_keys = {
        'appliedpaint': 'Applied Paint',
        'programmed': 'Programmed',
        'checkedresultcode': 'Checked   Result CODE',
    }

    def prepare(self):
        """Create initial data."""
        Part = self.old_state.apps.get_model('part', 'part')
        PartTestTemplate = self.old_state.apps.get_model('part', 'parttesttemplate')
        StockItem = self.old_state.apps.get_model('stock', 'stockitem')
        StockItemTestResult = self.old_state.apps.get_model(
            'stock', 'stockitemtestresult'
        )

        # Create a test part
        parent_part = Part.objects.create(
            name='Parent Part',
            description='A parent part',
            is_template=True,
            active=True,
            trackable=True,
            level=0,
            tree_id=1,
            lft=0,
            rght=0,
        )

        # Create some child parts
        children = [
            Part.objects.create(
                name=f'Child part {idx}',
                description='A child part',
                variant_of=parent_part,
                active=True,
                trackable=True,
                level=0,
                tree_id=1,
                lft=0,
                rght=0,
            )
            for idx in range(3)
        ]

        # Create some stock items
        for ii, child in enumerate(children):
            for jj in range(4):
                si = StockItem.objects.create(
                    part=child,
                    serial=str(1 + ii * jj),
                    quantity=1,
                    tree_id=0,
                    level=0,
                    lft=0,
                    rght=0,
                )

                # Create some test results
                for _k, v in self.test_keys.items():
                    StockItemTestResult.objects.create(
                        stock_item=si, test=v, result=True, value=f'Result: {ii} : {jj}'
                    )

        # Check initial record counts
        self.assertEqual(PartTestTemplate.objects.count(), 0)
        self.assertEqual(StockItemTestResult.objects.count(), 36)

    def test_migration(self):
        """Test that the migrations were applied as expected."""
        Part = self.new_state.apps.get_model('part', 'part')
        PartTestTemplate = self.new_state.apps.get_model('part', 'parttesttemplate')
        StockItem = self.new_state.apps.get_model('stock', 'stockitem')
        StockItemTestResult = self.new_state.apps.get_model(
            'stock', 'stockitemtestresult'
        )

        # Test that original record counts are correct
        self.assertEqual(Part.objects.count(), 4)
        self.assertEqual(StockItem.objects.count(), 12)
        self.assertEqual(StockItemTestResult.objects.count(), 36)

        # Two more test templates should have been created
        self.assertEqual(PartTestTemplate.objects.count(), 3)

        for k in self.test_keys.keys():
            self.assertTrue(PartTestTemplate.objects.filter(key=k).exists())

        for result in StockItemTestResult.objects.all():
            self.assertIsNotNone(result.template)
