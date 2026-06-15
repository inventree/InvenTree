"""Unit tests for the 'importer' app."""

import os

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
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
        for row in session.rows.all():
            self.assertIsNotNone(row.data.get('name', None))
            self.assertTrue(row.valid)

            row.validate(commit=True)
            self.assertTrue(row.complete)

        self.assertEqual(session.completed_row_count, 12)

        # Check that the new companies have been created
        self.assertEqual(n + 12, Company.objects.count())

    def test_field_defaults(self):
        """Test default field values."""


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
