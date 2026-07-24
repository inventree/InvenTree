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


class TestCreationDateMigration(MigratorTestCase):
    """Test the backfill data migration for StockItem.creation_date (stock.0121).

    The migration has two passes:
    - Pass 1: items with a CREATED (tracking_type=1) entry get creation_date from that entry.
    - Pass 2: remaining nulls get min(updated, stocktake_date, earliest_tracking_entry).

    Six scenarios are exercised to cover every meaningful code path.
    """

    migrate_from = ('stock', '0119_alter_stockitemtestresult_date')
    migrate_to = ('stock', '0122_alter_stockitem_creation_date')

    def prepare(self):
        """Create StockItem entries with varied data to exercise all backfill paths."""
        import datetime

        from django.db import connection

        Part = self.old_state.apps.get_model('part', 'part')
        StockItemTracking = self.old_state.apps.get_model('stock', 'stockitemtracking')

        utc = datetime.timezone.utc

        part = Part.objects.create(
            name='Migration Test Part', level=0, tree_id=1, lft=0, rght=0
        )

        def make_item(stocktake_date=None):
            """Insert a StockItem row via raw SQL, bypassing the duplicate-column ORM bug.

            The historical model at migration 0119 has status_custom_key enumerated twice
            (once from contribute_to_class on the status field, once from migration 0113's
            explicit AddField), so ORM-generated INSERTs fail with
            'column specified more than once'.  Raw SQL avoids the ORM field list entirely.
            Raw SQL also leaves updated=NULL (no DB-level default for auto_now), which
            makes Scenario 6 a clean "no date sources available" case.
            """
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO stock_stockitem
                        (part_id, quantity, level, tree_id, lft, rght,
                         status, delete_on_deplete, review_needed, is_building,
                         link, serial_int, barcode_data, barcode_hash)
                    VALUES (%s, 1, 0, 0, 0, 0, 10, false, false, false, '', 0, '', '')
                    RETURNING id
                    """,
                    [part.pk],
                )
                pk = cursor.fetchone()[0]
                if stocktake_date is not None:
                    cursor.execute(
                        'UPDATE stock_stockitem SET stocktake_date = %s WHERE id = %s',
                        [stocktake_date, pk],
                    )
            return pk

        def add_tracking(pk, tracking_type, date):
            """Create a tracking entry, then override its auto_now_add date."""
            entry = StockItemTracking.objects.create(
                item_id=pk, tracking_type=tracking_type
            )
            # auto_now_add prevents setting date on INSERT; use UPDATE to set a historical value
            StockItemTracking.objects.filter(pk=entry.pk).update(date=date)

        # --- Scenario 1 ---
        # Item with a single CREATED (type=1) tracking entry.
        # Pass 1 should set creation_date = that entry's date.
        pk = make_item()
        add_tracking(pk, 1, datetime.datetime(2022, 1, 15, 10, 0, 0, tzinfo=utc))
        self.pk_s1 = pk
        self.expected_s1 = datetime.datetime(2022, 1, 15, 10, 0, 0, tzinfo=utc)

        # --- Scenario 2 ---
        # Item with a CREATED entry (newer date) AND an older non-CREATED entry.
        # Pass 1 sets creation_date = CREATED entry date; older entry is ignored.
        # This verifies pass 1 wins over pass 2's min() logic.
        pk = make_item()
        add_tracking(
            pk, 1, datetime.datetime(2023, 6, 1, 0, 0, 0, tzinfo=utc)
        )  # CREATED, newer
        add_tracking(
            pk, 2, datetime.datetime(2018, 3, 10, 0, 0, 0, tzinfo=utc)
        )  # non-CREATED, older
        self.pk_s2 = pk
        self.expected_s2 = datetime.datetime(2023, 6, 1, 0, 0, 0, tzinfo=utc)
        self.rejected_s2 = datetime.date(2018, 3, 10)

        # --- Scenario 3 ---
        # Item with only non-CREATED tracking entries.
        # Pass 2 uses min(earliest_entry_date), so earliest entry wins.
        pk = make_item()
        add_tracking(
            pk, 2, datetime.datetime(2021, 7, 20, 0, 0, 0, tzinfo=utc)
        )  # later
        add_tracking(
            pk, 3, datetime.datetime(2020, 2, 14, 0, 0, 0, tzinfo=utc)
        )  # earliest
        self.pk_s3 = pk
        self.expected_s3 = datetime.datetime(2020, 2, 14, 0, 0, 0, tzinfo=utc)

        # --- Scenario 4 ---
        # Item with only stocktake_date set; no tracking entries.
        # Pass 2 uses stocktake_as_datetime (in the past) as the date.
        pk = make_item(stocktake_date=datetime.date(2019, 11, 5))
        self.pk_s4 = pk
        self.expected_s4_date = datetime.date(2019, 11, 5)

        # --- Scenario 5 ---
        # Item with stocktake_date AND a non-CREATED tracking entry where the tracking
        # entry is older than stocktake_date.
        # Pass 2 uses min(stocktake, tracking); tracking wins.
        pk = make_item(stocktake_date=datetime.date(2021, 4, 1))
        add_tracking(pk, 2, datetime.datetime(2017, 8, 22, 0, 0, 0, tzinfo=utc))
        self.pk_s5 = pk
        self.expected_s5 = datetime.datetime(2017, 8, 22, 0, 0, 0, tzinfo=utc)

        # --- Scenario 6 ---
        # Item inserted via raw SQL with no stocktake_date and no tracking entries,
        # so updated=NULL. No date sources exist → creation_date stays NULL after migration.
        pk = make_item()
        self.pk_s6 = pk

    def test_migration(self):
        """Verify creation_date is correctly backfilled for each scenario."""
        import datetime

        StockItem = self.new_state.apps.get_model('stock', 'stockitem')
        utc = datetime.timezone.utc

        def at_utc(dt):
            """Normalise to UTC and strip sub-second precision for comparison."""
            return dt.astimezone(utc).replace(microsecond=0)

        # Scenario 1: CREATED tracking entry → creation_date = entry date
        item = StockItem.objects.get(pk=self.pk_s1)
        self.assertIsNotNone(item.creation_date)
        self.assertEqual(at_utc(item.creation_date), self.expected_s1)

        # Scenario 2: CREATED entry (newer) wins over older non-CREATED entry
        item = StockItem.objects.get(pk=self.pk_s2)
        self.assertIsNotNone(item.creation_date)
        self.assertEqual(at_utc(item.creation_date), self.expected_s2)
        # Explicitly confirm the older non-CREATED date was NOT chosen
        self.assertNotEqual(item.creation_date.astimezone(utc).date(), self.rejected_s2)

        # Scenario 3: Earliest non-CREATED tracking entry wins (pass 2 min())
        item = StockItem.objects.get(pk=self.pk_s3)
        self.assertIsNotNone(item.creation_date)
        self.assertEqual(at_utc(item.creation_date), self.expected_s3)

        # Scenario 4: stocktake_date (past) wins over auto_now 'updated' (now)
        item = StockItem.objects.get(pk=self.pk_s4)
        self.assertIsNotNone(item.creation_date)
        self.assertEqual(
            item.creation_date.astimezone(utc).date(), self.expected_s4_date
        )

        # Scenario 5: Oldest tracking entry wins over stocktake_date (pass 2 min())
        item = StockItem.objects.get(pk=self.pk_s5)
        self.assertIsNotNone(item.creation_date)
        self.assertEqual(at_utc(item.creation_date), self.expected_s5)

        # Scenario 6: updated=NULL, no stocktake, no tracking → creation_date stays NULL
        item = StockItem.objects.get(pk=self.pk_s6)
        self.assertIsNone(item.creation_date)


class TestRemoveMpttFieldsMigration(MigratorTestCase):
    """Test data migration which removes MPTT fields (level, lft, rght, tree_id) from StockItem.

    The 'parent' field itself is untouched by this migration - only the MPTT
    bookkeeping fields are removed. This test ensures that parent-child
    relationships between StockItem objects survive the migration boundary.
    """

    migrate_from = ('stock', '0123_remove_stockitem_review_needed')
    migrate_to = ('stock', '0125_remove_mptt_fields')

    def prepare(self):
        """Create a tree of StockItem objects with parent-child relationships."""
        from django.db import connection

        Part = self.old_state.apps.get_model('part', 'part')
        StockItem = self.old_state.apps.get_model('stock', 'stockitem')

        part = Part.objects.create(
            name='Migration Test Part', level=0, tree_id=0, lft=0, rght=0
        )

        def make_item(quantity, parent_id=None):
            """Insert via raw SQL to avoid duplicate status_custom_key ORM bug."""
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO stock_stockitem
                        (part_id, quantity, level, tree_id, lft, rght,
                         status, delete_on_deplete, is_building,
                         link, serial_int, barcode_data, barcode_hash, parent_id)
                    VALUES (%s, %s, 0, 0, 0, 0, 10, false, false, '', 0, '', '', %s)
                    RETURNING id
                    """,
                    [part.pk, quantity, parent_id],
                )
                return cursor.fetchone()[0]

        # Root stock item, with no parent
        root_pk = make_item(100)

        # A set of child items, parented to the root item
        child_pks = [make_item(10, root_pk) for _ in range(3)]

        # A grandchild item, parented to the first child item
        grandchild_pk = make_item(1, child_pks[0])

        # An unrelated top-level item, with no parent
        orphan_pk = make_item(5)

        self.root_pk = root_pk
        self.child_pks = child_pks
        self.grandchild_pk = grandchild_pk
        self.orphan_pk = orphan_pk

        self.assertEqual(StockItem.objects.count(), 6)

    def test_migration(self):
        """Test that parent associations are preserved after MPTT fields are removed."""
        StockItem = self.new_state.apps.get_model('stock', 'stockitem')

        self.assertEqual(StockItem.objects.count(), 6)

        # The MPTT bookkeeping fields should no longer exist on the model
        field_names = {field.name for field in StockItem._meta.get_fields()}
        for removed_field in ['level', 'lft', 'rght', 'tree_id']:
            self.assertNotIn(removed_field, field_names)

        # The root item still has no parent
        root = StockItem.objects.get(pk=self.root_pk)
        self.assertIsNone(root.parent_id)

        # Each child item is still correctly parented to the root item
        for pk in self.child_pks:
            child = StockItem.objects.get(pk=pk)
            self.assertEqual(child.parent_id, self.root_pk)

        # The grandchild item is still correctly parented to the first child item
        grandchild = StockItem.objects.get(pk=self.grandchild_pk)
        self.assertEqual(grandchild.parent_id, self.child_pks[0])

        # The orphan item still has no parent
        orphan = StockItem.objects.get(pk=self.orphan_pk)
        self.assertIsNone(orphan.parent_id)
