"""Model definitions for the 'importer' app."""

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

import importer.validators
import InvenTree.helpers
from importer.status_codes import DataImportStatusCode


class DataImportSession(models.Model):
    """Database model representing a data import session.

    An initial file is uploaded, and used to populate the database.

    Fields:
        data_file: FileField for the data file to import
        status: IntegerField for the status of the import session
        user: ForeignKey to the User who initiated the import
        progress: IntegerField for the progress of the import (number of rows imported)
        data_columns: JSONField for the data columns in the import file (mapped to database columns)
        field_overrides: JSONField for field overrides (e.g. custom field values)
    """

    def save(self, *args, **kwargs):
        """Save the DataImportSession object."""
        if self.pk is None:
            # New object - run initial setup
            self.progress = 0
            self.auto_assign_columns()

        super().save(*args, **kwargs)

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

    progress = models.PositiveIntegerField(default=0, verbose_name=_('Progress'))

    data_columns = models.JSONField(
        blank=True, null=True, verbose_name=_('Data Columns')
    )

    field_defaults = models.JSONField(
        blank=True, null=True, verbose_name=_('Field Defaults')
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

        # TODO... implement auto mapping

        self.data_columns = column_map
