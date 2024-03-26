"""Model definitions for the 'importer' app."""

import logging
from typing import Collection

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError as DRFValidationError

import importer.operations
import importer.tasks
import importer.validators
import InvenTree.helpers
from importer.status_codes import DataImportStatusCode

logger = logging.getLogger('inventree')


class DataImportSession(models.Model):
    """Database model representing a data import session.

    An initial file is uploaded, and used to populate the database.

    Fields:
        timestamp: Timestamp for the import session
        data_file: FileField for the data file to import
        status: IntegerField for the status of the import session
        user: ForeignKey to the User who initiated the import
        field_defaults: JSONField for field overrides (e.g. custom field values)
    """

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the DataImportSession model."""
        return reverse('api-importer-session-list')

    def save(self, *args, **kwargs):
        """Save the DataImportSession object."""
        initial = self.pk is None

        self.clean()

        super().save(*args, **kwargs)

        if initial:
            # New object - run initial setup
            self.status = DataImportStatusCode.INITIAL.value
            self.progress = 0
            self.create_columns()

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
        blank=True,
        null=True,
        verbose_name=_('Field Defaults'),
        validators=[importer.validators.validate_field_defaults],
    )

    @property
    def field_mapping(self):
        """Construct a dict of field mappings for this import session.

        Returns: A dict of field: column mappings
        """
        mapping = {}

        if self.column_mappings.exists():
            for map in self.column_mappings.all():
                mapping[map.field] = map.column

        return mapping

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

    @property
    def columns(self) -> list:
        """Returns a list of the columns available for this data import session."""
        return [m.column for m in self.column_mappings.all()]

    def create_columns(self):
        """Generate column mappings based on the serializer fields.

        This method is called once, when the file is first imported.
        """
        # Extract list of column names from the file
        columns = importer.operations.extract_column_names(self.data_file)

        serializer_fields = self.serializer_fields(read_only=False)

        # Remove any existing mappings
        self.column_mappings.all().delete()

        matched_fields = set()

        column_mappings = []

        # Create a default mapping for each column in the dataset
        for column in columns:
            field_name = ''

            # Check each field for a direct match
            for field, field_def in serializer_fields.items():
                # Ignore if this field has already been matched to a column
                if field in matched_fields:
                    continue

                field_options = [field, getattr(field_def, 'label', field)]

                if column in field_options:
                    field_name = field
                    matched_fields.add(field)
                    break

                if column.lower() in [f.lower() for f in field_options]:
                    field_name = field
                    matched_fields.add(field)
                    break

            column_mappings.append(
                DataImportColumnMap(session=self, column=column, field=field_name)
            )

        # Create the column mappings
        DataImportColumnMap.objects.bulk_create(column_mappings)

        self.status = DataImportStatusCode.MAPPING.value
        self.save()

    def accept_mapping(self):
        """Accept current mapping configuration.

        - Validate that the current column mapping is correct
        - Trigger the data import process
        """
        # First, we need to ensure that all the *required* columns have been mapped
        required_fields = self.serializer_fields(required=True).keys()
        field_defaults = self.field_defaults or {}

        missing_fields = []

        for field in required_fields:
            # An explicit mapping exists
            if self.column_mappings.filter(field=field).exists():
                continue

            # A default value exists
            if field in field_defaults:
                continue

            missing_fields.append(field)

        if len(missing_fields) > 0:
            raise DjangoValidationError({
                'error': _('Some required fields have not been mapped'),
                'fields': missing_fields,
            })

        # No errors, so trigger the data import process
        self.trigger_data_import()

    def trigger_data_import(self):
        """Trigger the data import process for this session.

        Offloads the task to the background worker process.
        """
        from InvenTree.tasks import offload_task

        # Mark the import task status as "IMPORTING"
        self.status = DataImportStatusCode.IMPORTING.value
        self.save()

        offload_task(importer.tasks.import_data, self.pk)

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

    def available_fields(self):
        """Returns information on the available fields.

        - This method is designed to be introspected by the frontend, for rendering the various fields.
        - We make use of the InvenTree.metadata module to provide extra information about the fields.
        """
        from InvenTree.metadata import InvenTreeMetadata

        metadata = InvenTreeMetadata()
        if serializer := self.serializer:
            return metadata.get_serializer_info(serializer(data={}))
        else:
            return {}


class DataImportColumnMap(models.Model):
    """Database model representing a mapping between a file column and serializer field.

    - Each row maps a "column" (in the import file) to a "field" (in the serializer)
    - Column must exist in the file
    - Field must exist in the serializer (and not be read-only)
    """

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the DataImportColumnMap model."""
        return reverse('api-importer-mapping-list')

    def save(self, *args, **kwargs):
        """Save the DataImportColumnMap object."""
        self.clean()
        self.validate_unique()

        super().save(*args, **kwargs)

    def validate_unique(self, exclude=None):
        """Ensure that the column mapping is unique within the session."""
        super().validate_unique(exclude)

        columns = self.session.column_mappings.exclude(pk=self.pk)

        if columns.filter(column=self.column).exists():
            raise DjangoValidationError({'column': _('Column is already mapped')})

        if self.field not in ['', None] and columns.filter(field=self.field).exists():
            raise DjangoValidationError({'field': _('Field is already mapped')})

    def clean(self):
        """Validate the column mapping."""
        super().clean()

        if not self.session:
            raise DjangoValidationError({
                'session': _('Column mapping must be linked to a valid import session')
            })

        if self.column not in self.session.columns:
            raise DjangoValidationError({
                'column': _('Column does not exist in the data file')
            })

        # Field is allowed to be empty
        if self.field in ['', None]:
            return

        field_def = self.field_definition

        if not field_def:
            raise DjangoValidationError({
                'field': _('Field does not exist in the target model')
            })

        if field_def.read_only:
            raise DjangoValidationError({'field': _('Selected field is read-only')})

    @property
    def field_definition(self):
        """Return the field definition associated with this column mapping."""
        fields = self.session.serializer_fields(read_only=None)
        return fields.get(self.field, None)

    session = models.ForeignKey(
        DataImportSession,
        on_delete=models.CASCADE,
        verbose_name=_('Import Session'),
        related_name='column_mappings',
    )

    column = models.CharField(max_length=100, verbose_name=_('Column'))

    field = models.CharField(blank=True, max_length=100, verbose_name=_('Field'))

    @property
    def label(self):
        """Extract the 'label' associated with the mapped field."""
        field_def = self.field_definition

        if field_def:
            return field_def.label

        # Default to the field name
        return self.field


class DataImportRow(models.Model):
    """Database model representing a single row in a data import session.

    Each row corresponds to a single row in the import file, and is used to populate the database.

    Fields:
        session: ForeignKey to the parent DataImportSession object
        data: JSONField for the data in this row
        status: IntegerField for the status of the row import
    """

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the DataImportRow model."""
        return reverse('api-importer-row-list')

    def save(self, *args, **kwargs):
        """Save the DataImportRow object."""
        self.valid = self.validate()
        super().save(*args, **kwargs)

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

    valid = models.BooleanField(default=False, verbose_name=_('Valid'))

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

    def serializer_data(self):
        """Construct data object to be sent to the serializer.

        Note that we also use the "default" values provided by the import session
        """
        session_defaults = self.session.field_defaults or {}

        return {**session_defaults, **self.data}

    def construct_serializer(self):
        """Construct a serializer object for this row."""
        serializer_class = self.session.serializer

        if not serializer_class:
            return None

        return serializer_class(data=self.serializer_data())

    def validate(self) -> bool:
        """Validate the data in this row against the linked serializer.

        Returns:
            True if the data is valid, False otherwise

        Raises:
            ValidationError: If the linked serializer is not valid
        """
        serializer = self.construct_serializer()

        if not serializer:
            self.errors = {
                'non_field_errors': 'No serializer class linked to this import session'
            }
            return

        result = False

        try:
            result = serializer.is_valid(raise_exception=True)
        except (DjangoValidationError, DRFValidationError) as e:
            self.errors = e.detail

        if result:
            self.errors = None

        return result
