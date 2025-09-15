"""Unit tests for the 'importer' app."""

import os

from django.core.files.base import ContentFile
from django.urls import reverse

from importer.models import DataImportRow, DataImportSession
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

        self.assertEqual(session.column_mappings.count(), 15)

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
