"""Unit tests for the 'importer' app."""

import datetime
import os
import threading
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import connection
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse

from importer.models import DataImportColumnMap, DataImportRow, DataImportSession
from InvenTree.unit_test import AdminTestCase, InvenTreeAPITestCase, InvenTreeTestCase


class ImporterMixin:
    """Helpers for import tests."""

    def helper_file(self, fn: str) -> ContentFile:
        """Return test data."""
        file_path = os.path.join(os.path.dirname(__file__), 'test_data', fn)

        with open(file_path, encoding='utf-8') as input_file:
            data = input_file.read()

        return ContentFile(data, fn)


class ImporterTest(ImporterMixin, InvenTreeTestCase):
    """Basic tests for file imports."""

    def test_import_session(self):
        """Test creation of a data import session."""
        from company.models import Company

        n = Company.objects.count()

        data_file = self.helper_file('companies.csv')

        session = DataImportSession.objects.create(
            data_file=data_file, model_type='company'
        )

        session.extract_columns()

        self.assertEqual(session.column_mappings.count(), 14)

        # Check some of the field mappings
        for field, col in [
            ('website', 'Website'),
            ('is_customer', 'Is customer'),
            ('phone', 'Phone number'),
            ('description', 'Company description'),
            ('active', 'Active'),
        ]:
            self.assertTrue(
                session.column_mappings.filter(field=field, column=col).exists()
            )

        # Run the data import
        session.import_data()
        self.assertEqual(session.rows.count(), 12)

        # Check that some data has been imported
        rows = list(session.rows.all())
        self.assertEqual(len(rows), 12)

        for row in rows:
            self.assertIsNotNone(row.data.get('name', None))
            self.assertTrue(row.valid)

            row.validate(commit=True)
            self.assertTrue(row.complete)

        # All rows accepted: rows and mappings are cleared, session is retained
        session.refresh_from_db()
        self.assertEqual(session.rows.count(), 0)
        self.assertEqual(session.column_mappings.count(), 0)

        # Check that the new companies have been created
        self.assertEqual(n + 12, Company.objects.count())

    def test_row_data_datetime_serialization(self):
        """Test that row data containing native datetime values can be saved.

        Regression test for a Sentry crash: "Object of type datetime is not JSON
        serializable when serializing dict item 'COMMENT'". Excel imports (via
        tablib/openpyxl) return date-formatted cells as native datetime.datetime
        objects rather than strings. These flow unmodified into row_data, which
        is then persisted via DataImportRow.objects.bulk_create().

        DataImportRow.row_data / data / errors (and the related JSONFields on
        DataImportSession) previously had no `encoder=DjangoJSONEncoder`, so
        Django's JSONField fell back to the plain stdlib json.JSONEncoder, which
        cannot serialize datetime objects - raising a TypeError on save/bulk_create.
        """
        data_file = self.helper_file('companies.csv')

        session = DataImportSession.objects.create(
            data_file=data_file, model_type='company'
        )

        row = DataImportRow(
            session=session,
            row_index=0,
            row_data={'COMMENT': datetime.datetime(2024, 5, 1, 12, 30)},
        )

        # This must not raise: TypeError: Object of type datetime is not JSON serializable
        DataImportRow.objects.bulk_create([row])
        row = DataImportRow.objects.get(session=session, row_index=0)
        self.assertEqual(row.row_data['COMMENT'], '2024-05-01T12:30:00')

    def test_import_header_whitespace(self):
        """Test that column headers with leading/trailing whitespace are handled correctly.

        Regression test: column mappings are built from *stripped* header names, but
        row data was previously extracted using the *raw* (unstripped) headers. If a
        header had surrounding whitespace, the mapped column name would never match a
        key in the row data, so that field was silently skipped during import.
        """
        from company.models import Company

        n = Company.objects.count()

        # Pad each header in the source file with extra whitespace
        raw = self.helper_file('companies.csv').read()
        lines = raw.splitlines()
        headers = [f'  {header}  ' for header in lines[0].split(',')]
        padded_data = '\n'.join([','.join(headers), *lines[1:]])

        data_file = ContentFile(padded_data, 'companies_whitespace.csv')

        session = DataImportSession.objects.create(
            data_file=data_file, model_type='company'
        )

        session.extract_columns()

        # Extracted column names should have whitespace stripped
        for col in session.columns:
            self.assertEqual(col, col.strip())

        # Field mappings should be created correctly, against the *stripped* names
        for field, col in [
            ('website', 'Website'),
            ('is_customer', 'Is customer'),
            ('phone', 'Phone number'),
            ('description', 'Company description'),
            ('active', 'Active'),
        ]:
            self.assertTrue(
                session.column_mappings.filter(field=field, column=col).exists()
            )

        # Run the data import
        session.import_data()
        self.assertEqual(session.rows.count(), 12)

        rows = list(session.rows.all())

        # Row data keys must be stripped, to match the mapped column names
        for row in rows:
            for key in row.row_data:
                self.assertEqual(key, key.strip())

        # Find the 'Arrow' row, and check that mapped fields were actually extracted
        arrow_row = next(row for row in rows if row.data.get('name') == 'Arrow')
        self.assertEqual(arrow_row.data.get('website'), 'https://www.arrow.com/')
        self.assertEqual(arrow_row.data.get('description'), 'Arrow Electronics')
        self.assertEqual(arrow_row.data.get('is_customer'), False)

        for row in rows:
            self.assertIsNotNone(row.data.get('name', None))
            self.assertTrue(row.valid)

            row.validate(commit=True)
            self.assertTrue(row.complete)

        # All rows accepted: rows and mappings are cleared, session is retained
        session.refresh_from_db()
        self.assertEqual(session.rows.count(), 0)
        self.assertEqual(session.column_mappings.count(), 0)

        # Check that the new companies have been created
        self.assertEqual(n + 12, Company.objects.count())

    def test_import_encoding(self):
        """Test that non-UTF-8 encoded data files are handled correctly.

        Regression test: CSV files exported from Excel on Windows are commonly
        encoded as cp1252 rather than utf-8. Previously, an unhandled
        UnicodeDecodeError was raised (surfaced to the user as a server error)
        instead of a well-formed ValidationError.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        raw = self.helper_file('companies.csv').read()

        # Encode the file data as cp1252, including a character not valid in utf-8
        lines = raw.splitlines()
        lines[1] = lines[1].replace('Arrow Electronics', 'Arrow Electronics \xb2')
        cp1252_data = '\n'.join(lines).encode('cp1252')

        data_file = ContentFile(cp1252_data, 'companies_cp1252.csv')

        session = DataImportSession.objects.create(
            data_file=data_file, model_type='company'
        )

        session.extract_columns()
        session.import_data()

        arrow_row = next(
            row for row in session.rows.all() if row.data.get('name') == 'Arrow'
        )
        self.assertEqual(arrow_row.data.get('description'), 'Arrow Electronics ²')

        # A file containing bytes which are not valid in either utf-8 or cp1252
        # should raise a ValidationError, rather than an unhandled exception
        invalid_data = ContentFile(b'name,website\r\n\x81\x8d,test\r\n', 'invalid.csv')

        with self.assertRaises(DjangoValidationError):
            DataImportSession.objects.create(
                data_file=invalid_data, model_type='company'
            ).extract_columns()

    def test_field_defaults(self):
        """Test default field values.

        Regression test for bug #30 (dev/todo/bugs.md): validate_field_defaults
        must reject any parsed JSON value that isn't actually a dict, not just
        values which fail to parse as JSON at all.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        def data_file():
            # full_clean() reads the file eagerly, so each session needs its own
            # freshly-opened (binary) copy
            content = self.helper_file('companies.csv').read()
            return ContentFile(content.encode(), 'companies.csv')

        # A dict value is accepted as-is
        session = DataImportSession(
            data_file=data_file(), model_type='company', field_defaults={'name': 'Test'}
        )
        session.full_clean()

        # A JSON-encoded dict string is also accepted (de-stringified)
        session = DataImportSession(
            data_file=data_file(),
            model_type='company',
            field_defaults='{"name": "Test"}',
        )
        session.full_clean()

        # A JSON-encoded list is valid JSON, but not a dict - must be rejected
        session = DataImportSession(
            data_file=data_file(), model_type='company', field_defaults='[1, 2, 3]'
        )
        with self.assertRaises(DjangoValidationError):
            session.full_clean()

        # Garbage which does not even parse as JSON must also be rejected
        session = DataImportSession(
            data_file=data_file(), model_type='company', field_defaults='not valid json'
        )
        with self.assertRaises(DjangoValidationError):
            session.full_clean()

    def test_update_existing_records(self):
        """Test updating existing records via import, providing only the ID field.

        Regression test for GH #12499: when updating existing records, only the
        primary key should be required. Fields which are not mapped to a column
        (and have no explicit override/default) must:
        - not be flagged as "required" and block the mapping wizard
        - not be auto-populated with a model-level "creation" default
        - not overwrite the existing value on the target record
        """
        from part.models import Part, PartCategory
        from stock.models import StockItem

        category = PartCategory.objects.create(
            name='Update Test Category', description='Test category'
        )
        part = Part.objects.create(
            category=category, name='Update Test Part', description='Test part'
        )

        item = StockItem.objects.create(part=part, quantity=42, batch='Original batch')

        csv_content = f'ID,batch\n{item.pk},Updated batch\n'
        data_file = ContentFile(csv_content, 'stock_update.csv')

        session = DataImportSession.objects.create(
            data_file=data_file, model_type='stockitem', update_records=True
        )

        # Only the 'id' field should be required - 'quantity' and 'part' already
        # exist on the target record, and must not be forced
        required = session.required_fields()
        self.assertIn('id', required)
        self.assertNotIn('quantity', required)
        self.assertNotIn('part', required)

        # No model-level "creation" default should have been auto-populated for
        # 'quantity' - doing so would silently overwrite the existing value
        self.assertNotIn('quantity', session.field_defaults or {})

        # Mapping is valid, even though 'quantity' and 'part' are unmapped
        session.accept_mapping()

        session.refresh_from_db()
        self.assertEqual(session.rows.count(), 1)

        row = session.rows.first()
        self.assertTrue(row.valid)

        # Unmapped fields must not appear in the extracted row data at all
        self.assertNotIn('quantity', row.data)
        self.assertNotIn('part', row.data)

        self.assertTrue(row.validate(commit=True))
        self.assertTrue(row.complete)

        # Existing values for unmapped fields must be preserved
        item.refresh_from_db()
        self.assertEqual(item.quantity, 42)
        self.assertEqual(item.part, part)
        self.assertEqual(item.batch, 'Updated batch')

    def test_lookup_field_ambiguous_match(self):
        """Test the behavior of lookup_related_field for ambiguous and pinned matches."""
        from django.core.exceptions import ValidationError as DjangoValidationError

        from part.models import Part, PartCategory

        category = PartCategory.objects.create(
            name='Test Category', description='Test category'
        )

        # Two parts which collide under different IMPORT_ID_FIELDS ('IPN' and 'name')
        part_a = Part.objects.create(
            category=category, name='Widget', description='desc', IPN='AMBIG-001'
        )
        Part.objects.create(
            category=category, name='AMBIG-001', description='desc', IPN='WIDGET-002'
        )

        data_file = self.helper_file('companies.csv')
        session = DataImportSession.objects.create(
            data_file=data_file, model_type='stockitem'
        )

        row = DataImportRow(session=session)
        row.related_field_map = {}

        # Auto-lookup (no pinned lookup field) raises, as the value matches two different parts
        with self.assertRaises(DjangoValidationError):
            row.lookup_related_field('part', 'AMBIG-001')

        # Pinning the lookup field to 'IPN' resolves the match unambiguously
        result = row.lookup_related_field('part', 'AMBIG-001', lookup_field='IPN')
        self.assertEqual(result, part_a.pk)

        # Pinning the lookup field to 'name' resolves to the *other* part
        result = row.lookup_related_field('part', 'AMBIG-001', lookup_field='name')
        self.assertNotEqual(result, part_a.pk)

    def test_extract_data_related_field_validation_error(self):
        """Test that extract_data() handles a dict-constructed ValidationError.

        Regression test: django.core.exceptions.ValidationError only exposes a
        `.message` attribute when it was raised with a single message string.
        lookup_related_field can also raise with a dict (e.g. "no related model
        found for field") or a list, in which case `.message` does not exist and
        accessing it raises: AttributeError: 'ValidationError' object has no
        attribute 'message'. extract_data() must use `.messages` instead, which
        normalizes any construction to a flat list of strings.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        data_file = self.helper_file('companies.csv')
        session = DataImportSession.objects.create(
            data_file=data_file, model_type='stockitem'
        )

        row = DataImportRow(session=session, row_data={'Website': 'foo'})

        field_mapping = {'part': 'Website'}
        available_fields = {'part': {'type': 'related field'}}

        with mock.patch.object(
            DataImportRow,
            'lookup_related_field',
            side_effect=DjangoValidationError({
                'session': 'No related model found for field: part'
            }),
        ):
            # Must not raise: AttributeError: 'ValidationError' object has no attribute 'message'
            row.extract_data(
                field_mapping=field_mapping,
                available_fields=available_fields,
                commit=False,
            )

        self.assertEqual(row.errors, {'part': 'No related model found for field: part'})

    def test_lookup_field_validation(self):
        """Test that DataImportColumnMap.clean() validates the lookup_field value."""
        from django.core.exceptions import ValidationError as DjangoValidationError

        data_file = self.helper_file('companies.csv')
        session = DataImportSession.objects.create(
            data_file=data_file, model_type='stockitem'
        )

        part_mapping = session.column_mappings.get(field='part')
        quantity_mapping = session.column_mappings.get(field='quantity')

        # Valid lookup field for a related (FK) field
        part_mapping.lookup_field = 'IPN'
        part_mapping.save()
        part_mapping.refresh_from_db()
        self.assertEqual(part_mapping.lookup_field, 'IPN')

        # Invalid lookup field (not a valid IMPORT_ID_FIELDS option)
        part_mapping.lookup_field = 'not_a_real_field'
        with self.assertRaises(DjangoValidationError):
            part_mapping.save()

        # lookup_field cannot be set against a non-related field
        quantity_mapping.lookup_field = 'IPN'
        with self.assertRaises(DjangoValidationError):
            quantity_mapping.save()


@skipUnlessDBFeature('has_select_for_update')
class DataImportRowConcurrencyTest(ImporterMixin, TransactionTestCase):
    """Genuine cross-transaction regression test for row locking during a data-import update.

    Uses two real threads (each with its own database connection) to reproduce the
    lost-update race: two concurrent import rows updating *different* fields on the
    same StockItem could both read the pre-update instance before either had
    committed its save() - and since save() writes the *entire* instance, whichever
    thread committed second would silently discard the first thread's change.

    DataImportRow.validate() now locks the target row (select_for_update, inside
    transaction.atomic()) for the duration of the read-modify-write cycle, so the
    second thread's read is forced to wait until the first thread's transaction
    commits - and therefore sees (and preserves) the first thread's change.
    """

    def setUp(self):
        """Create a single StockItem to update concurrently."""
        super().setUp()

        from part.models import Part, PartCategory
        from stock.models import StockItem

        category = PartCategory.objects.create(
            name='Concurrency Category', description='Test category'
        )
        self.part = Part.objects.create(
            category=category, name='Concurrency Part', description='Test part'
        )
        self.item = StockItem.objects.create(part=self.part, quantity=10)

    def helper_session(self) -> DataImportSession:
        """Construct a minimal DataImportSession configured for stock item updates."""
        return DataImportSession.objects.create(
            data_file=self.helper_file('companies.csv'),
            model_type='stockitem',
            update_records=True,
        )

    def test_concurrent_update_does_not_lose_writes(self):
        """Two concurrent updates to different fields must not clobber one another."""
        start_barrier = threading.Barrier(2, timeout=5)
        errors = []

        # Wrap DataImportRow._get_update_instance() so both threads reach the
        # (real, database-level) row lock at the same time - one wins the lock
        # and proceeds through to commit, the other blocks until the winner's
        # transaction completes.
        original_get_update_instance = DataImportRow._get_update_instance

        def synced_get_update_instance(row, instance_id, queryset):
            start_barrier.wait(timeout=5)
            return original_get_update_instance(row, instance_id, queryset)

        def update(field, value):
            try:
                row = DataImportRow(
                    session=self.helper_session(),
                    # 'part' is a required field on StockItemSerializer, so it must
                    # be included even though this row is only actually changing
                    # 'field' - the fix under test is *locking*, not partial-update
                    # support, so we work within the serializer's existing rules
                    data={'id': self.item.pk, 'part': self.part.pk, field: value},
                )
                if not row.validate(commit=True):
                    errors.append(row.errors)
            except Exception as exc:  # pragma: no cover - surfaced via errors list
                errors.append(exc)
            finally:
                connection.close()

        with mock.patch.object(
            DataImportRow, '_get_update_instance', synced_get_update_instance
        ):
            # Note: 'batch' is deliberately avoided here - it has a model-level
            # default (generate_batch_code), and DRF applies a field's default to
            # *any* non-partial update where the field is omitted, regardless of
            # the existing instance value. That's a separate, already-tracked
            # issue (GH #12499) and would confound this test, which is only
            # about proving the row lock closes the read/write race.
            thread_a = threading.Thread(target=update, args=('notes', 'notes-a'))
            thread_b = threading.Thread(
                target=update, args=('packaging', 'packaging-b')
            )

            thread_a.start()
            thread_b.start()
            thread_a.join(timeout=10)
            thread_b.join(timeout=10)

        self.assertEqual(errors, [])

        self.item.refresh_from_db()
        self.assertEqual(self.item.notes, 'notes-a')
        self.assertEqual(self.item.packaging, 'packaging-b')


class ImportAPITest(ImporterMixin, InvenTreeAPITestCase):
    """End-to-end tests for the importer API."""

    def test_import(self):
        """Test full import process via the API."""
        from part.models import PartCategory

        N = PartCategory.objects.count()

        url = reverse('api-importer-session-list')

        # Load data file
        data_file = self.helper_file('part_categories.csv')

        data = self.post(
            url,
            {'model_type': 'partcategory', 'data_file': data_file},
            format='multipart',
        ).data

        self.assertFalse(data['update_records'])
        self.assertEqual(data['model_type'], 'partcategory')

        # No data has been imported yet
        self.assertEqual(data['row_count'], 0)
        self.assertEqual(data['completed_row_count'], 0)

        field_names = data['available_fields'].keys()

        for fn in ['name', 'default_location', 'description']:
            self.assertIn(fn, field_names)

        self.assertEqual(len(data['columns']), 14)
        for col in ['Name', 'Parent Category', 'Path']:
            self.assertIn(col, data['columns'])

        session_id = data['pk']

        # Accept the field mappings
        url = reverse('api-import-session-accept-fields', kwargs={'pk': session_id})

        # Initially the user does not have the right permissions
        self.post(url, expected_code=403)

        # Assign correct permission to user
        self.assignRole('part_category.add')

        self.post(url, expected_code=200)

        session = self.get(
            reverse('api-import-session-detail', kwargs={'pk': session_id})
        ).data

        self.assertEqual(session['row_count'], 5)
        self.assertEqual(session['completed_row_count'], 0)

        # Fetch each row, and validate it
        rows = self.get(
            reverse('api-importer-row-list'), data={'session': session_id}
        ).data

        self.assertEqual(len(rows), 5)

        row_ids = []

        for row in rows:
            row_ids.append(row['pk'])
            self.assertEqual(row['session'], session_id)
            self.assertTrue(row['valid'])
            self.assertFalse(row['complete'])

        # Validate the rows
        url = reverse('api-import-session-accept-rows', kwargs={'pk': session_id})

        self.post(
            url,
            {
                'rows': row_ids[1:]  # Validate all but the first row
            },
        )

        # Update session information
        session = self.get(
            reverse('api-import-session-detail', kwargs={'pk': session_id})
        ).data

        self.assertEqual(session['row_count'], 5)
        self.assertEqual(session['completed_row_count'], 4)

        for idx, row in enumerate(row_ids):
            detail = self.get(
                reverse('api-importer-row-detail', kwargs={'pk': row})
            ).data

            self.assertEqual(detail['session'], session_id)
            self.assertEqual(detail['complete'], idx > 0)

        # Check that there are new database records
        self.assertEqual(PartCategory.objects.count(), N + 4)

    def test_column_mapping_lookup_field(self):
        """Test that the 'lookup_field' option can be specified via the column-mapping API."""
        f = self.helper_file('companies.csv')

        session = DataImportSession.objects.create(
            data_file=f, model_type='stockitem', user=self.user
        )

        self.assignRole('stock.change')

        # available_fields should expose the valid lookup field options for the 'part' FK field
        session_detail = self.get(
            reverse('api-import-session-detail', kwargs={'pk': session.pk})
        ).data
        part_field_info = session_detail['available_fields']['part']
        self.assertIn('lookup_fields', part_field_info)
        self.assertIn('IPN', part_field_info['lookup_fields'])
        self.assertIn('name', part_field_info['lookup_fields'])
        self.assertIn('pk', part_field_info['lookup_fields'])

        part_mapping = session.column_mappings.get(field='part')
        quantity_mapping = session.column_mappings.get(field='quantity')

        mapping_url = reverse(
            'api-importer-mapping-detail', kwargs={'pk': part_mapping.pk}
        )

        # Initially, no lookup field is set (defaults to 'auto')
        data = self.get(mapping_url).data
        self.assertIn(data['lookup_field'], [None, ''])

        # Set a valid lookup field
        data = self.patch(mapping_url, {'lookup_field': 'IPN'}, expected_code=200).data
        self.assertEqual(data['lookup_field'], 'IPN')

        # Confirm it persists
        data = self.get(mapping_url).data
        self.assertEqual(data['lookup_field'], 'IPN')

        # An invalid lookup field is rejected
        self.patch(mapping_url, {'lookup_field': 'not_a_real_field'}, expected_code=400)

        # Clear the lookup field (revert to 'auto')
        data = self.patch(mapping_url, {'lookup_field': None}, expected_code=200).data
        self.assertIn(data['lookup_field'], [None, ''])

        # lookup_field cannot be set against a non-related field
        quantity_url = reverse(
            'api-importer-mapping-detail', kwargs={'pk': quantity_mapping.pk}
        )
        self.patch(quantity_url, {'lookup_field': 'IPN'}, expected_code=400)

    def test_session_list(self):
        """Test API endpoint which details the list of import sessions."""
        url = reverse('api-importer-session-list')

        # Construct a dummy file
        f = self.helper_file('companies.csv')

        for ii in range(5):
            DataImportSession.objects.create(
                data_file=f,
                model_type='company',
                user=self.user if ii % 2 == 0 else None,
            )

        # Staff user should see all sessions
        self.user.is_staff = True
        self.user.save()

        response = self.get(url)
        self.assertEqual(len(response.data), 5)

        # Non-staff user should only see sessions which they own
        self.user.is_staff = False
        self.user.save()

        response = self.get(url)
        self.assertEqual(len(response.data), 3)
        for session in response.data:
            self.assertEqual(session['user'], self.user.pk)

    def test_accept_fields_ownership(self):
        """Test that accept_fields rejects requests for sessions owned by another user."""
        other_user = User.objects.create_user(
            username='other_accept', password='password'
        )

        f = self.helper_file('companies.csv')
        session = DataImportSession.objects.create(
            data_file=f, model_type='company', user=other_user
        )

        url = reverse('api-import-session-accept-fields', kwargs={'pk': session.pk})

        # Non-owner, non-staff should be denied
        self.user.is_staff = False
        self.user.save()
        self.post(url, expected_code=403)

        # Staff should be allowed (subject to model permission)
        # Company is part of the purchase_order ruleset
        self.user.is_staff = True
        self.user.save()
        self.assignRole('purchase_order.change')
        self.post(url, expected_code=200)

    def test_accept_rows_ownership(self):
        """Test that accept_rows rejects requests for sessions owned by another user."""
        other_user = User.objects.create_user(
            username='other_accept_rows', password='password'
        )

        f = self.helper_file('companies.csv')
        session = DataImportSession.objects.create(
            data_file=f, model_type='company', user=other_user
        )
        session.extract_columns()

        url = reverse('api-import-session-accept-rows', kwargs={'pk': session.pk})

        self.user.is_staff = False
        self.user.save()
        self.post(url, {'rows': []}, expected_code=403)

        # Staff can reach the endpoint (rows list is empty so validation rejects with 400, not 403)
        self.user.is_staff = True
        self.user.save()
        self.post(url, {'rows': []}, expected_code=400)

    def test_session_cleanup_on_complete(self):
        """Test that a completed import session deletes itself and all associated data."""
        url = reverse('api-importer-session-list')
        data_file = self.helper_file('part_categories.csv')

        data = self.post(
            url,
            {'model_type': 'partcategory', 'data_file': data_file},
            format='multipart',
        ).data

        session_id = data['pk']
        session_pk = session_id

        self.assignRole('part_category.add')
        self.post(
            reverse('api-import-session-accept-fields', kwargs={'pk': session_id}),
            expected_code=200,
        )

        rows = self.get(
            reverse('api-importer-row-list'), data={'session': session_id}
        ).data
        row_ids = [r['pk'] for r in rows]
        self.assertGreater(len(row_ids), 0)

        # Confirm rows and mappings exist before acceptance
        self.assertTrue(DataImportRow.objects.filter(session_id=session_pk).exists())
        self.assertTrue(
            DataImportColumnMap.objects.filter(session_id=session_pk).exists()
        )

        # Accept all rows — this should trigger cleanup of rows and mappings
        self.post(
            reverse('api-import-session-accept-rows', kwargs={'pk': session_id}),
            {'rows': row_ids},
        )

        # Rows and column mappings must be cleared
        self.assertFalse(DataImportRow.objects.filter(session_id=session_pk).exists())
        self.assertFalse(
            DataImportColumnMap.objects.filter(session_id=session_pk).exists()
        )

        # Session itself is retained as an audit record with COMPLETE status
        from importer.models import DataImportSession
        from importer.status_codes import DataImportStatusCode

        session_obj = DataImportSession.objects.get(pk=session_pk)
        self.assertEqual(session_obj.status, DataImportStatusCode.COMPLETE.value)

        detail = self.get(
            reverse('api-import-session-detail', kwargs={'pk': session_id}),
            expected_code=200,
        ).data
        self.assertEqual(detail['row_count'], 0)
        self.assertEqual(detail['completed_row_count'], 0)

    def test_row_and_mapping_ownership(self):
        """Test that DataImportRow and DataImportColumnMap endpoints filter by session ownership."""
        f = self.helper_file('companies.csv')

        other_user = User.objects.create_user(
            username='other_importer', password='password'
        )

        # Session owned by self.user
        session_mine = DataImportSession.objects.create(
            data_file=f, model_type='company', user=self.user
        )
        session_mine.extract_columns()

        # Session owned by another user
        f2 = self.helper_file('companies.csv')
        session_other = DataImportSession.objects.create(
            data_file=f2, model_type='company', user=other_user
        )
        session_other.extract_columns()

        row_list_url = reverse('api-importer-row-list')
        mapping_list_url = reverse('api-importer-mapping-list')

        # Non-staff: should only see rows/mappings from own session
        self.user.is_staff = False
        self.user.save()

        rows = self.get(row_list_url).data
        for row in rows:
            self.assertEqual(row['session'], session_mine.pk)

        mappings = self.get(mapping_list_url).data
        for mapping in mappings:
            self.assertEqual(mapping['session'], session_mine.pk)

        # Detail endpoint: own session's row/mapping should be accessible
        own_row = DataImportRow.objects.filter(session=session_mine).first()
        other_row = DataImportRow.objects.filter(session=session_other).first()

        if own_row:
            self.get(
                reverse('api-importer-row-detail', kwargs={'pk': own_row.pk}),
                expected_code=200,
            )
        if other_row:
            self.get(
                reverse('api-importer-row-detail', kwargs={'pk': other_row.pk}),
                expected_code=404,
            )

        own_mapping = DataImportColumnMap.objects.filter(session=session_mine).first()
        other_mapping = DataImportColumnMap.objects.filter(
            session=session_other
        ).first()

        if own_mapping:
            self.get(
                reverse('api-importer-mapping-detail', kwargs={'pk': own_mapping.pk}),
                expected_code=200,
            )
        if other_mapping:
            self.get(
                reverse('api-importer-mapping-detail', kwargs={'pk': other_mapping.pk}),
                expected_code=404,
            )

        # Staff user: should see rows/mappings from all sessions
        self.user.is_staff = True
        self.user.save()

        all_row_pks = set(DataImportRow.objects.values_list('pk', flat=True))
        response_rows = self.get(row_list_url).data
        self.assertEqual({r['pk'] for r in response_rows}, all_row_pks)

        all_mapping_pks = set(DataImportColumnMap.objects.values_list('pk', flat=True))
        response_mappings = self.get(mapping_list_url).data
        self.assertEqual({m['pk'] for m in response_mappings}, all_mapping_pks)


class AdminTest(ImporterMixin, AdminTestCase):
    """Tests for the admin interface integration."""

    def test_admin(self):
        """Test the admin URL."""
        data_file = self.helper_file('companies.csv')

        session = self.helper(
            model=DataImportSession,
            model_kwargs={'data_file': data_file, 'model_type': 'company'},
        )
        self.helper(model=DataImportRow, model_kwargs={'session_id': session.id})
