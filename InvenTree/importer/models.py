"""Model definitions for the 'importer' app."""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError as DRFValidationError

import importer.operations
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
            self.extract_column_names()
            self.auto_assign_columns()
            self.save()

            self.trigger_data_import()

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

    columns = models.JSONField(blank=True, null=True, verbose_name=_('Columns'))

    def extract_column_names(self):
        """Extract column names from uploaded file.

        This method is called once, when the file is first uploaded.
        """
        self.columns = importer.operations.extract_column_names(self.data_file)

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
        available_columns = self.columns
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

    def trigger_data_import(self):
        """Trigger the data import process for this session.

        Offloads the task to the background worker process.
        """
        from importer.tasks import import_data
        from InvenTree.tasks import offload_task

        offload_task(import_data, self.pk)

    def import_data(self):
        """Perform the data import process for this session."""
        # TODO: Clear any existing error messages

        # Clear any existing data rows
        self.rows.all().delete()

        df = importer.operations.load_data_file(self.data_file)

        if df is None:
            # TODO: Log an error message against the import session
            logger.error('Failed to load data file')
            return

        headers = df.headers

        row_objects = []

        # Mark the import task status as "IMPORTING"
        self.status = DataImportStatusCode.IMPORTING.value
        self.save()

        # Iterate through each "row" in the data file, and create a new DataImportRow object
        for idx, row in enumerate(df):
            row_data = dict(zip(headers, row))

            row_objects.append(
                importer.models.DataImportRow(
                    session=self, row_data=row_data, row_index=idx
                )
            )

        # Finally, create the DataImportRow objects
        importer.models.DataImportRow.objects.bulk_create(row_objects)

        # Mark the import task as "PROCESSING"
        self.status = DataImportStatusCode.PROCESSING.value
        self.save()

        # Set initial data and errors for each row
        for row in self.rows.all():
            row.extract_data(field_mapping=self.field_mapping)
            row.validate()

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

    def extract_data(self, field_mapping: dict = None):
        """Extract row data from the provided data dictionary."""
        if not field_mapping:
            field_mapping = self.session.field_mapping

        data = {}

        # We have mapped column (file) to field (serializer) already
        for field, col in field_mapping.items():
            data[field] = self.row_data.get(col, None)

        self.data = data
        self.save()

    def set_errors(self, errors: dict) -> None:
        """Set the error messages for this row."""
        self.errors = errors
        self.save()

    def validate(self, raise_exception=True) -> bool:
        """Validate the data in this row against the linked serializer.

        Returns:
            True if the data is valid, False otherwise

        Raises:
            ValidationError: If the linked serializer is not valid
        """
        serializer_class = self.session.serializer if self.session else None

        if not serializer_class:
            self.set_errors({
                'non_field_errors': 'No serializer class linked to this import session'
            })
            return

        result = False

        try:
            serializer = serializer_class(data=self.data)
            result = serializer.is_valid(raise_exception=raise_exception)
        except (DjangoValidationError, DRFValidationError) as e:
            self.set_errors(e.detail)

        return result
