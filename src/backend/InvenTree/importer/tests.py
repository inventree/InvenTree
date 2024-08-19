"""Unit tests for the 'importer' app."""

import os

from django.core.files.base import ContentFile

from importer.models import DataImportSession
from InvenTree.unit_test import InvenTreeTestCase


class ImporterTest(InvenTreeTestCase):
    """Basic tests for file imports."""

    def test_import_session(self):
        """Test creation of a data import session."""
        from company.models import Company

        n = Company.objects.count()

        fn = os.path.join(os.path.dirname(__file__), 'test_data', 'companies.csv')

        with open(fn, encoding='utf-8') as input_file:
            data = input_file.read()

        session = DataImportSession.objects.create(
            data_file=ContentFile(data, 'companies.csv'), model_type='company'
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
