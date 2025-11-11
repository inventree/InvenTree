"""Model definitions for the 'importer' app."""

import json
from collections import OrderedDict
from typing import Optional

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from rest_framework.exceptions import ValidationError as DRFValidationError

import importer.operations
import importer.registry
import importer.tasks
import importer.validators
import InvenTree.helpers
from common.models import RenderChoices
from importer.status_codes import DataImportStatusCode

logger = structlog.get_logger('inventree')


class DataImportSession(models.Model):
    """Database model representing a data import session.

    An initial file is uploaded, and used to populate the database.

    Fields:
        timestamp: Timestamp for the import session
        data_file: FileField for the data file to import
        status: IntegerField for the status of the import session
        user: ForeignKey to the User who initiated the import
        field_defaults: JSONField for field default values - provides a backup value for a field
        field_overrides: JSONField for field override values - used to force a value for a field
        field_filters: JSONField for field filter values - optional field API filters
    """

    ID_FIELD_LABEL = 'id'

    class ModelChoices(RenderChoices):
        """Model choices for data import sessions."""

        choice_fnc = importer.registry.supported_models

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
            self.extract_columns()

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

    model_type = models.CharField(
        blank=False,
        max_length=100,
        validators=[importer.validators.validate_importer_model_type],
        verbose_name=_('Model Type'),
        help_text=_('Target model type for this import session'),
    )

    status = models.PositiveIntegerField(
        default=DataImportStatusCode.INITIAL.value,
        choices=DataImportStatusCode.items(),
        help_text=_('Import status'),
    )

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_('User')
    )

    field_defaults = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Field Defaults'),
        validators=[importer.validators.validate_field_defaults],
    )

    field_overrides = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Field Overrides'),
        validators=[importer.validators.validate_field_defaults],
    )

    field_filters = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Field Filters'),
        validators=[importer.validators.validate_field_defaults],
    )

    update_records = models.BooleanField(
        default=False,
        verbose_name=_('Update Existing Records'),
        help_text=_('If enabled, existing records will be updated with new data'),
    )

    @property
    def field_mapping(self) -> dict:
        """Construct a dict of field mappings for this import session.

        Returns:
            A dict of field -> column mappings
        """
        return {mapping.field: mapping.column for mapping in self.column_mappings.all()}

    @property
    def model_class(self):
        """Return the model class for this importer."""
        serializer = self.serializer_class

        if serializer:
            return serializer.Meta.model

    @property
    def serializer_class(self):
        """Return the serializer class for this importer."""
        from importer.registry import supported_models

        return supported_models().get(self.model_type, None)

    def extract_columns(self) -> None:
        """Run initial column extraction and mapping.

        This method is called when the import session is first created.

        - Extract column names from the data file
        - Create a default mapping for each field in the serializer
        - Find a default "backup" value for each field (if one exists)
        """
        # Extract list of column names from the file
        self.columns = importer.operations.extract_column_names(self.data_file)

        serializer_fields = self.available_fields()

        # Remove any existing mappings
        self.column_mappings.all().delete()

        column_mappings = []

        matched_columns = set()

        self.field_defaults = self.field_defaults or {}
        field_overrides = self.field_overrides or {}

        # Create a default mapping for each available field in the database
        for field, field_def in serializer_fields.items():
            # If an override value is provided for the field,
            # skip creating a mapping for this field
            if field in field_overrides:
                continue

            # Extract a "default" value for the field, if one exists
            # Skip if one has already been provided by the user
            if field not in self.field_defaults and 'default' in field_def:
                self.field_defaults[field] = field_def['default']

            # Generate a list of possible column names for this field
            field_options = [
                field,
                field_def.get('label', field),
                field_def.get('help_text', field),
            ]
            column_name = ''

            for column in self.columns:
                # No title provided for the column
                if not column:
                    continue

                # Ignore if we have already matched this column to a field
                if column in matched_columns:
                    continue

                # Try direct match
                if column in field_options:
                    column_name = column
                    break

                # Try lower case match
                if column.lower() in [f.lower() for f in field_options]:
                    column_name = column
                    break

            column_mappings.append(
                DataImportColumnMap(session=self, column=column_name, field=field)
            )

        # Create the column mappings
        DataImportColumnMap.objects.bulk_create(column_mappings)

        self.status = DataImportStatusCode.MAPPING.value
        self.save()

    def accept_mapping(self) -> None:
        """Accept current mapping configuration.

        - Validate that the current column mapping is correct
        - Trigger the data import process
        """
        # First, we need to ensure that all the *required* columns have been mapped
        required_fields = self.required_fields()

        field_defaults = self.field_defaults or {}
        field_overrides = self.field_overrides or {}

        missing_fields = []

        for field in required_fields:
            # An override value exists
            if field in field_overrides:
                continue

            # A default value exists
            if field_defaults.get(field):
                continue

            # The field has been mapped to a data column
            if mapping := self.column_mappings.filter(field=field).first():
                if mapping.column:
                    continue

            missing_fields.append(field)

        if len(missing_fields) > 0:
            raise DjangoValidationError({
                'error': _('Some required fields have not been mapped'),
                'fields': missing_fields,
            })

        # No errors, so trigger the data import process
        self.trigger_data_import()

    def trigger_data_import(self) -> None:
        """Trigger the data import process for this session.

        Offloads the task to the background worker process.
        """
        from InvenTree.tasks import offload_task

        # Mark the import task status as "IMPORTING"
        self.status = DataImportStatusCode.IMPORTING.value
        self.save()

        offload_task(importer.tasks.import_data, self.pk, group='importer')

    def import_data(self) -> None:
        """Perform the data import process for this session."""
        # Clear any existing data rows
        self.rows.all().delete()

        df = importer.operations.load_data_file(self.data_file)

        if df is None:
            # TODO: Log an error message against the import session
            logger.error('Failed to load data file')
            return

        headers = df.headers

        imported_rows = []

        field_mapping = self.field_mapping
        available_fields = self.available_fields()

        # Iterate through each "row" in the data file, and create a new DataImportRow object
        for idx, row in enumerate(df):
            row_data = dict(zip(headers, row, strict=False))

            # Skip completely empty rows
            if not any(row_data.values()):
                continue

            row = DataImportRow(session=self, row_data=row_data, row_index=idx)

            row.extract_data(
                field_mapping=field_mapping,
                available_fields=available_fields,
                commit=False,
            )

            row.valid = row.validate(commit=False)
            imported_rows.append(row)

        # Perform database writes as a single operation
        DataImportRow.objects.bulk_create(imported_rows)

        # Mark the import task as "PROCESSING"
        self.status = DataImportStatusCode.PROCESSING.value
        self.save()

    def check_complete(self) -> bool:
        """Check if the import session is complete."""
        if self.completed_row_count < self.row_count:
            return False

        # Update the status of this session
        if self.status != DataImportStatusCode.COMPLETE.value:
            self.status = DataImportStatusCode.COMPLETE.value
            self.save()

        return True

    @property
    def row_count(self) -> int:
        """Return the number of rows in the import session."""
        return self.rows.count()

    @property
    def completed_row_count(self) -> int:
        """Return the number of completed rows for this session."""
        return self.rows.filter(complete=True).count()

    def available_fields(self):
        """Returns information on the available fields.

        - This method is designed to be introspected by the frontend, for rendering the various fields.
        - We make use of the InvenTree.metadata module to provide extra information about the fields.

        Note that we cache these fields, as they are expensive to compute.
        """
        if fields := getattr(self, '_available_fields', None):
            return fields

        from InvenTree.metadata import InvenTreeMetadata

        metadata = InvenTreeMetadata()

        fields = OrderedDict()

        if self.update_records:
            # If we are updating records, ensure the ID field is included
            fields[self.ID_FIELD_LABEL] = {
                'label': _('ID'),
                'help_text': _('Existing database identifier for the record'),
                'type': 'integer',
                'required': True,
                'read_only': False,
            }

        if serializer_class := self.serializer_class:
            serializer = serializer_class(data={}, importing=True)
            fields.update(metadata.get_serializer_info(serializer))

        # Cache the available fields against this instance
        self._available_fields = fields

        return fields

    def required_fields(self) -> dict:
        """Returns information on which fields are *required* for import."""
        fields = self.available_fields()

        required = {}

        for field, info in fields.items():
            if info.get('required', False):
                required[field] = info

            elif self.update_records and field == self.ID_FIELD_LABEL:
                # If we are updating records, the ID field is required
                required[field] = info

        return required


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

        if (
            self.column not in ['', None]
            and columns.filter(column=self.column).exists()
        ):
            raise DjangoValidationError({
                'column': _('Column is already mapped to a database field')
            })

        if columns.filter(field=self.field).exists():
            raise DjangoValidationError({
                'field': _('Field is already mapped to a data column')
            })

    def clean(self):
        """Validate the column mapping."""
        super().clean()

        if not self.session:
            raise DjangoValidationError({
                'session': _('Column mapping must be linked to a valid import session')
            })

        if self.column and self.column not in self.session.columns:
            raise DjangoValidationError({
                'column': _('Column does not exist in the data file')
            })

        field_def = self.field_definition

        if not field_def:
            raise DjangoValidationError({
                'field': _('Field does not exist in the target model')
            })

        if field_def.get('read_only', False):
            raise DjangoValidationError({'field': _('Selected field is read-only')})

    session = models.ForeignKey(
        DataImportSession,
        on_delete=models.CASCADE,
        verbose_name=_('Import Session'),
        related_name='column_mappings',
    )

    field = models.CharField(max_length=100, verbose_name=_('Field'))

    column = models.CharField(blank=True, max_length=100, verbose_name=_('Column'))

    @property
    def available_fields(self):
        """Return a list of available fields for this import session.

        These fields get cached, as they are expensive to compute.
        """
        if fields := getattr(self, '_available_fields', None):
            return fields

        self._available_fields = self.session.available_fields()

        return self._available_fields

    @property
    def field_definition(self):
        """Return the field definition associated with this column mapping."""
        fields = self.available_fields
        return fields.get(self.field, None)

    @property
    def label(self):
        """Extract the 'label' associated with the mapped field."""
        if field_def := self.field_definition:
            return field_def.get('label', None)

    @property
    def description(self):
        """Extract the 'description' associated with the mapped field."""
        description = None

        if field_def := self.field_definition:
            description = field_def.get('help_text', None)

        if not description:
            description = self.label

        return description


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

    @property
    def default_values(self) -> dict:
        """Return a dict object of the 'default' values for this row."""
        defaults = self.session.field_defaults or {}

        if type(defaults) is not dict:
            try:
                defaults = json.loads(str(defaults))
            except json.JSONDecodeError:
                logger.warning('Failed to parse default values for import row')
                defaults = {}

        return defaults

    @property
    def override_values(self) -> dict:
        """Return a dict object of the 'override' values for this row."""
        overrides = self.session.field_overrides or {}

        if type(overrides) is not dict:
            try:
                overrides = json.loads(str(overrides))
            except json.JSONDecodeError:
                logger.warning('Failed to parse override values for import row')
                overrides = {}

        return overrides

    def extract_data(
        self,
        available_fields: Optional[dict] = None,
        field_mapping: Optional[dict] = None,
        commit=True,
    ):
        """Extract row data from the provided data dictionary."""
        if not field_mapping:
            field_mapping = self.session.field_mapping

        if not available_fields:
            available_fields = self.session.available_fields()

        override_values = self.override_values
        default_values = self.default_values

        data = {}

        # We have mapped column (file) to field (serializer) already
        for field, col in field_mapping.items():
            # Data override (force value and skip any further checks)
            if field in override_values:
                data[field] = override_values[field]
                continue

            # Default value (if provided)
            if field in default_values:
                data[field] = default_values[field]

            # If this field is *not* mapped to any column, skip
            if not col or col not in self.row_data:
                continue

            # Extract field type
            field_def = available_fields.get(field, {})

            field_type = field_def.get('type', None)

            value = self.row_data.get(col, None)

            if field_type == 'boolean':
                value = InvenTree.helpers.str2bool(value)
            elif field_type == 'date':
                value = value or None

            # Use the default value, if provided
            if value is None and field in default_values:
                value = default_values[field]

            # If the field provides a set of valid 'choices', use that as a lookup
            if field_type == 'choice' and 'choices' in field_def:
                choices = field_def.get('choices', None)

                if callable(choices):
                    choices = choices()

                # Try to match the provided value against the available choices
                choice_value = None

                for choice in choices:
                    primary_value = choice['value']
                    display_value = choice['display_name']

                    if primary_value == value:
                        choice_value = primary_value
                        # Break on first match against a primary choice value
                        break

                    if display_value == value:
                        choice_value = primary_value

                    elif (
                        str(display_value).lower().strip() == str(value).lower().strip()
                        and choice_value is None
                    ):
                        # Case-insensitive match against display value
                        choice_value = primary_value

                if choice_value is not None:
                    value = choice_value

            data[field] = value

        self.data = data

        if commit:
            self.save()

    def serializer_data(self):
        """Construct data object to be sent to the serializer.

        - If available, we use the "default" values provided by the import session
        - If available, we use the "override" values provided by the import session
        """
        data = {}

        data.update(self.default_values)

        if self.data:
            data.update(self.data)

        # Override values take priority, if present
        data.update(self.override_values)

        return data

    def construct_serializer(self, instance=None, request=None):
        """Construct a serializer object for this row."""
        if serializer_class := self.session.serializer_class:
            return serializer_class(
                instance=instance,
                data=self.serializer_data(),
                context={'request': request},
            )

    def validate(self, commit=False, request=None) -> bool:
        """Validate the data in this row against the linked serializer.

        Arguments:
            commit: If True, the data is saved to the database (if validation passes)
            request: The request object (if available) for extracting user information

        Returns:
            True if the data is valid, False otherwise

        Raises:
            ValidationError: If the linked serializer is not valid
        """
        if self.complete:
            # Row has already been completed
            return True

        if self.session.update_records:
            # Extract the ID field from the data
            instance_id = self.data.get(self.session.ID_FIELD_LABEL, None)

            if not instance_id:
                raise DjangoValidationError(
                    _('ID is required for updating existing records.')
                )

            try:
                instance = self.session.model_class.objects.get(pk=instance_id)
            except self.session.model_class.DoesNotExist:
                self.errors = {
                    'non_field_errors': _('No record found with the provided ID')
                    + f': {instance_id}'
                }
                return False
            except ValueError:
                self.errors = {
                    'non_field_errors': _('Invalid ID format provided')
                    + f': {instance_id}'
                }
                return False
            except Exception as e:
                self.errors = {'non_field_errors': str(e)}
                return False

            serializer = self.construct_serializer(instance=instance, request=request)

        else:
            serializer = self.construct_serializer(request=request)

        if not serializer:
            self.errors = {
                'non_field_errors': 'No serializer class linked to this import session'
            }
            return False

        result = False

        try:
            result = serializer.is_valid(raise_exception=True)
        except (DjangoValidationError, DRFValidationError) as e:
            self.errors = e.detail

        if result:
            self.errors = None

            if commit:
                try:
                    serializer.save()
                    self.complete = True

                except ValueError as e:  # Exception as e:
                    self.errors = {'non_field_errors': str(e)}
                    result = False

                self.save()
                self.session.check_complete()

        return result
