"""Model definitions for the 'importer' app."""

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

import importer.validators
import InvenTree.helpers
from importer.status_codes import DataImportStatusCode


class DataImportSession(models.Model):
    """Database model representing a data import session.

    An initial file is uploaded, and used to populate the database.

    Fields:
        timestamp: Timestamp for the import session
        data_file: FileField for the data file to import
        status: IntegerField for the status of the import session
        user: ForeignKey to the User who initiated the import
        data_columns: JSONField for the data columns in the import file (mapped to database columns)
        field_overrides: JSONField for field overrides (e.g. custom field values)
    """

    def save(self, *args, **kwargs):
        """Save the DataImportSession object."""
        initial = self.pk is None

        self.clean()

        super().save(*args, **kwargs)

        if initial:
            # New object - run initial setup
            self.status = DataImportStatusCode.INITIAL.value
            self.progress = 0
            self.create_rows()
            self.auto_assign_columns()
            self.save()

    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('Timestamp'))

    data_file = models.FileField(
        upload_to='import',
        verbose_name=_('Data File'),
        help_text=_('Data file to import'),
        validators=[
            FileExtensionValidator(
                allowed_extensions=InvenTree.helpers.GetExportFormats()
            ),
            importer.validators.validate_data_file,
        ],
    )

    model_type = models.CharField(
        blank=False,
        max_length=100,
        validators=[importer.validators.validate_importer_model_type],
    )

    status = models.PositiveIntegerField(
        default=DataImportStatusCode.INITIAL.value,
        choices=DataImportStatusCode.items(),
        help_text=_('Import status'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('User')
    )

    field_defaults = models.JSONField(
        blank=True, null=True, verbose_name=_('Field Defaults')
    )

    field_mapping = models.JSONField(
        blank=True, null=True, verbose_name=_('Field Mapping')
    )

    @property
    def serializer(self):
        """Return the serializer class for this importer."""
        from importer.registry import supported_models

        return supported_models().get(self.model_type, None)

    def serializer_fields(self, required=None, read_only=False):
        """Return the writeable serializers fields for this importer.

        Arguments:
            required: If True, only return required fields
        """
        from importer.operations import get_fields

        return get_fields(self.serializer, required=required, read_only=read_only)

    def auto_assign_columns(self):
        """Automatically assign columns based on the serializer fields."""
        from importer.operations import extract_column_names

        available_columns = extract_column_names(self.data_file)
        serializer_fields = self.serializer_fields()

        # Create a mapping of column names to serializer fields
        column_map = {}

        for name, field in serializer_fields.items():
            column = None
            label = getattr(field, 'label', name)

            if name in available_columns:
                column = name
            elif label in available_columns:
                column = label

            column_map[name] = column

        self.field_mapping = column_map

    @transaction.atomic
    def create_rows(self):
        """Generate DataImportRow objects for each row in the import file."""
        from importer.operations import extract_rows

        # Remove any existing rows
        self.rows.all().delete()

        for idx, row in enumerate(extract_rows(self.data_file)):
            DataImportRow.objects.create(session=self, data=row, row_index=idx)

    @property
    def row_count(self):
        """Return the number of rows in the import session."""
        return self.rows.count()

    @property
    def completed_row_count(self):
        """Return the number of completed rows for this session."""
        if self.row_count == 0:
            return 0

        return self.rows.filter(complete=True).count() / self.row_count * 100


class DataImportRow(models.Model):
    """Database model representing a single row in a data import session.

    Each row corresponds to a single row in the import file, and is used to populate the database.

    Fields:
        session: ForeignKey to the parent DataImportSession object
        data: JSONField for the data in this row
        status: IntegerField for the status of the row import
    """

    session = models.ForeignKey(
        DataImportSession,
        on_delete=models.CASCADE,
        verbose_name=_('Import Session'),
        related_name='rows',
    )

    row_index = models.PositiveIntegerField(default=0, verbose_name=_('Row Index'))

    row_data = models.JSONField(
        blank=True, null=True, verbose_name=_('Original row data')
    )

    data = models.JSONField(blank=True, null=True, verbose_name=_('Data'))

    errors = models.JSONField(blank=True, null=True, verbose_name=_('Errors'))

    complete = models.BooleanField(default=False, verbose_name=_('Complete'))
