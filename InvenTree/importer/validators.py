"""Custom validation routines for the 'importer' app."""

import os

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Define maximum limits for imported file data
IMPORTER_MAX_FILE_SIZE = 32 * 1024 * 1042
IMPORTER_MAX_ROWS = 1000
IMPORTER_MAX_COLS = 1000


def validate_data_file(data_file):
    """Validate the provided data file."""
    import importer.operations

    filesize = data_file.size
    filetype = os.path.splitext(data_file.name)[1]

    if filesize > IMPORTER_MAX_FILE_SIZE:
        raise ValidationError(_('Data file exceeds maximum size limit'))

    dataset = importer.operations.load_data_file(data_file.file, format=filetype)

    if len(dataset.headers) > IMPORTER_MAX_COLS:
        raise ValidationError(_('Data file contains too many columns'))

    if len(dataset) > IMPORTER_MAX_ROWS:
        raise ValidationError(_('Data file contains too many rows'))


def validate_importer_model_type(value):
    """Validate that the given model type is supported for importing."""
    from importer.registry import supported_models

    if value not in supported_models().keys():
        raise ValidationError(f"Unsupported model type '{value}'")
