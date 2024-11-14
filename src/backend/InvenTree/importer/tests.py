"""Unit tests for the 'importer' app."""

import os

from django.core.files.base import ContentFile

from importer.models import DataImportRow, DataImportSession
from InvenTree.unit_test import AdminTestCase, InvenTreeTestCase


class ImporterMixin:
    """Helpers for import tests."""

    def helper_file(self):
        """Return test data."""
        fn = os.path.join(os.path.dirname(__file__), 'test_data', 'companies.csv')

        with open(fn, encoding='utf-8') as input_file:
            data = input_file.read()
        return data

    def helper_content(self):
        """Return content file."""
        return ContentFile(self.helper_file(), 'companies.csv')


class ImporterTest(ImporterMixin, InvenTreeTestCase):
    """Basic tests for file imports."""

    def test_import_session(self):
        """Test creation of a data import session."""
        from company.models import Company

        n = Company.objects.count()

        session = DataImportSession.objects.create(
            data_file=self.helper_content(), model_type='company'
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


class AdminTest(ImporterMixin, AdminTestCase):
    """Tests for the admin interface integration."""

    def test_admin(self):
        """Test the admin URL."""
        session = self.helper(
            model=DataImportSession,
            model_kwargs={'data_file': self.helper_content(), 'model_type': 'company'},
        )
        self.helper(model=DataImportRow, model_kwargs={'session_id': session.id})
