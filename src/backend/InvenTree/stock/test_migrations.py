"""Unit tests for data migrations in the 'stock' app."""

from django_test_migrations.contrib.unittest_case import MigratorTestCase


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

        from django.conf import settings
        from django.db import connection

        Part = self.old_state.apps.get_model('part', 'part')
        StockItemTracking = self.old_state.apps.get_model('stock', 'stockitemtracking')

        utc = datetime.timezone.utc if settings.USE_TZ else None

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
            insert_sql = """
                INSERT INTO stock_stockitem
                    (part_id, quantity, level, tree_id, lft, rght,
                     status, delete_on_deplete, review_needed, is_building,
                     link, serial_int, barcode_data, barcode_hash)
                VALUES (%s, 1, 0, 0, 0, 0, 10, false, false, false, '', 0, '', '')
                """
            with connection.cursor() as cursor:
                # MySQL has no RETURNING support at all (not even a syntax error
                # workaround) - fall back to cursor.lastrowid there, and use
                # RETURNING elsewhere since psycopg's cursor has no lastrowid.
                if connection.features.can_return_rows_from_bulk_insert:
                    cursor.execute(insert_sql + 'RETURNING id', [part.pk])
                    pk = cursor.fetchone()[0]
                else:
                    cursor.execute(insert_sql, [part.pk])
                    pk = cursor.lastrowid
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

        from django.conf import settings

        StockItem = self.new_state.apps.get_model('stock', 'stockitem')
        utc = datetime.timezone.utc if settings.USE_TZ else None

        def at_utc(dt):
            """Normalise to UTC and strip sub-second precision for comparison."""
            return (
                dt.astimezone(utc).replace(microsecond=0)
                if settings.USE_TZ
                else dt.replace(microsecond=0)
            )

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
            insert_sql = """
                INSERT INTO stock_stockitem
                    (part_id, quantity, level, tree_id, lft, rght,
                     status, delete_on_deplete, is_building,
                     link, serial_int, barcode_data, barcode_hash, parent_id)
                VALUES (%s, %s, 0, 0, 0, 0, 10, false, false, '', 0, '', '', %s)
                """
            with connection.cursor() as cursor:
                # MySQL has no RETURNING support at all - fall back to
                # cursor.lastrowid there, and use RETURNING elsewhere since
                # psycopg's cursor has no lastrowid.
                if connection.features.can_return_rows_from_bulk_insert:
                    cursor.execute(
                        insert_sql + 'RETURNING id', [part.pk, quantity, parent_id]
                    )
                    return cursor.fetchone()[0]
                cursor.execute(insert_sql, [part.pk, quantity, parent_id])
                return cursor.lastrowid

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
