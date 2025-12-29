"""Unit tests for data migrations in the 'stock' app."""

from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestSerialNumberMigration(MigratorTestCase):
    """Test data migration which updates serial numbers."""

    migrate_from = ('stock', '0067_alter_stockitem_part')
    migrate_to = ('stock', '0070_auto_20211128_0151')

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
    migrate_to = ('stock', '0073_alter_stockitem_belongs_to')

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
                for v in self.test_keys.values():
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

        for k in self.test_keys:
            self.assertTrue(PartTestTemplate.objects.filter(key=k).exists())

        for result in StockItemTestResult.objects.all():
            self.assertIsNotNone(result.template)


class TestPathstringMigration(MigratorTestCase):
    """Unit tests for StockLocation.Pathstring data migrations."""

    migrate_from = ('stock', '0080_stocklocation_pathstring')
    migrate_to = ('stock', '0081_auto_20220801_0044')

    def prepare(self):
        """Create initial data."""
        StockLocation = self.old_state.apps.get_model('stock', 'stocklocation')

        # Create a test StockLocation
        loc1 = StockLocation.objects.create(
            name='Loc 1', level=0, lft=0, rght=0, tree_id=0
        )
        loc2 = StockLocation.objects.create(
            name='Loc 2', parent=loc1, level=1, lft=0, rght=0, tree_id=0
        )
        StockLocation.objects.create(
            name='Loc 3', parent=loc2, level=2, lft=0, rght=0, tree_id=0
        )
        StockLocation.objects.create(name='Loc 4', level=0, lft=0, rght=0, tree_id=0)

        # Check initial record counts
        self.assertEqual(StockLocation.objects.count(), 4)

    def test_migration(self):
        """Test that the migrations were applied as expected."""
        StockLocation = self.old_state.apps.get_model('stock', 'stocklocation')

        self.assertEqual(StockLocation.objects.count(), 4)
        test_data = {
            'Loc 1': 'Loc 1',
            'Loc 2': 'Loc 1/Loc 2',
            'Loc 3': 'Loc 1/Loc 2/Loc 3',
            'Loc 4': 'Loc 4',
        }
        for loc_name, pathstring in test_data.items():
            loc = StockLocation.objects.get(name=loc_name)
            self.assertEqual(loc.pathstring, pathstring)


class TestBarcodeToUidMigration(MigratorTestCase):
    """Unit tests for barcode to uid data migrations."""

    migrate_from = ('stock', '0084_auto_20220903_0154')
    migrate_to = ('stock', '0085_auto_20220903_0225')

    def prepare(self):
        """Create initial data."""
        Part = self.old_state.apps.get_model('part', 'part')
        StockItem = self.old_state.apps.get_model('stock', 'stockitem')

        # Create a test StockItem
        part = Part.objects.create(name='test', level=0, lft=0, rght=0, tree_id=0)
        StockItem.objects.create(
            part_id=part.id, uid='12345', level=0, lft=0, rght=0, tree_id=0
        )
        self.assertEqual(StockItem.objects.count(), 1)

    def test_migration(self):
        """Test that the migrations were applied as expected."""
        StockItem = self.new_state.apps.get_model('stock', 'StockItem')

        self.assertEqual(StockItem.objects.count(), 1)
        item = StockItem.objects.first()
        self.assertEqual(item.barcode_hash, '12345')
        self.assertEqual(item.uid, '12345')


class TestBarcodeToUiReversedMigration(MigratorTestCase):
    """Unit tests for barcode to uid data migrations."""

    migrate_to = ('stock', '0084_auto_20220903_0154')
    migrate_from = ('stock', '0085_auto_20220903_0225')

    def prepare(self):
        """Create initial data."""
        Part = self.old_state.apps.get_model('part', 'part')
        StockItem = self.old_state.apps.get_model('stock', 'stockitem')

        # Create a test StockItem
        part = Part.objects.create(name='test', level=0, lft=0, rght=0, tree_id=0)
        StockItem.objects.create(
            part_id=part.id, barcode_hash='54321', level=0, lft=0, rght=0, tree_id=0
        )
        self.assertEqual(StockItem.objects.count(), 1)

    def test_migration(self):
        """Test that the migrations were applied as expected."""
        StockItem = self.new_state.apps.get_model('stock', 'StockItem')

        self.assertEqual(StockItem.objects.count(), 1)
        item = StockItem.objects.first()
        self.assertEqual(item.barcode_hash, '54321')
        self.assertEqual(item.uid, '54321')


class TestPartTestTemplateTreeFixMigration(MigratorTestCase):
    """Unit tests for fixing issues with PartTestTemplate tree branch confusion migrations."""

    migrate_from = ('stock', '0107_remove_stockitemtestresult_test_and_more')
    migrate_to = ('stock', '0108_auto_20240219_0252')

    def prepare(self):
        """Create initial data."""
        Part = self.old_state.apps.get_model('part', 'part')
        PartTestTemplate = self.old_state.apps.get_model('part', 'PartTestTemplate')
        StockItem = self.old_state.apps.get_model('stock', 'StockItem')
        StockItemTestResult = self.old_state.apps.get_model(
            'stock', 'StockItemTestResult'
        )

        p = Part.objects.create(name='test', level=0, lft=0, rght=0, tree_id=0)
        p2 = Part.objects.create(name='test 2', level=0, lft=0, rght=0, tree_id=4)
        tmpl = PartTestTemplate.objects.create(part=p2, key='test_key')
        stock = StockItem.objects.create(part=p, level=0, lft=3, rght=0, tree_id=0)
        StockItemTestResult.objects.create(template=tmpl, stock_item=stock)
        self.assertEqual(StockItemTestResult.objects.count(), 1)
        self.assertEqual(PartTestTemplate.objects.count(), 1)

    def test_migration(self):
        """Test that the migrations were applied as expected."""
        PartTestTemplate = self.old_state.apps.get_model('part', 'PartTestTemplate')
        StockItemTestResult = self.old_state.apps.get_model(
            'stock', 'StockItemTestResult'
        )

        self.assertEqual(StockItemTestResult.objects.count(), 1)
        self.assertEqual(PartTestTemplate.objects.count(), 2)


class TestStockItemTrackingMigration(MigratorTestCase):
    """Unit tests for StockItemTracking code migrations."""

    migrate_from = ('stock', '0095_stocklocation_external')
    migrate_to = ('stock', '0096_auto_20230330_1121')

    def prepare(self):
        """Create initial data."""
        from stock.status_codes import StockHistoryCode

        Part = self.old_state.apps.get_model('part', 'part')
        SalesOrder = self.old_state.apps.get_model('order', 'salesorder')
        StockItem = self.old_state.apps.get_model('stock', 'stockitem')
        StockItemTracking = self.old_state.apps.get_model('stock', 'stockitemtracking')

        # Create a test StockItem
        part = Part.objects.create(name='test', level=0, lft=0, rght=0, tree_id=0)
        so = SalesOrder.objects.create(reference='123')
        si = StockItem.objects.create(
            part_id=part.id, sales_order=so, level=0, lft=0, rght=0, tree_id=0
        )
        si2 = StockItem.objects.create(
            part_id=part.id, sales_order=so, level=0, lft=0, rght=0, tree_id=0
        )
        StockItem.objects.create(
            part_id=part.id, sales_order=so, level=0, lft=0, rght=0, tree_id=0
        )

        StockItemTracking.objects.create(
            item_id=si.pk,
            tracking_type=StockHistoryCode.SENT_TO_CUSTOMER.value,
            deltas={'foo': 'bar'},
        )
        StockItemTracking.objects.create(
            item_id=si2.pk,
            tracking_type=StockHistoryCode.SHIPPED_AGAINST_SALES_ORDER.value,
            deltas={'foo': 'bar'},
        )
        self.assertEqual(StockItemTracking.objects.count(), 2)

    def test_migration(self):
        """Test that the migrations were applied as expected."""
        from stock.status_codes import StockHistoryCode

        StockItemTracking = self.old_state.apps.get_model('stock', 'stockitemtracking')

        self.assertEqual(StockItemTracking.objects.count(), 2)
        item = StockItemTracking.objects.first()
        self.assertEqual(
            item.tracking_type, StockHistoryCode.SHIPPED_AGAINST_SALES_ORDER
        )
        self.assertIn('salesorder', item.deltas)
        self.assertEqual(item.deltas['salesorder'], 1)
