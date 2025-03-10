"""Custom validation routines for the 'importer' app."""

import json

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Define maximum limits for imported file data
IMPORTER_MAX_FILE_SIZE = 32 * 1024 * 1042
IMPORTER_MAX_ROWS = 5000
IMPORTER_MAX_COLS = 1000


def validate_data_file(data_file):
    """Validate the provided data file."""
    import importer.operations

    filesize = data_file.size

    if filesize > IMPORTER_MAX_FILE_SIZE:
        raise ValidationError(_('Data file exceeds maximum size limit'))

    dataset = importer.operations.load_data_file(data_file)

    if not dataset.headers or len(dataset.headers) == 0:
        raise ValidationError(_('Data file contains no headers'))

    if len(dataset.headers) > IMPORTER_MAX_COLS:
        raise ValidationError(_('Data file contains too many columns'))

    if len(dataset) > IMPORTER_MAX_ROWS:
        raise ValidationError(_('Data file contains too many rows'))


def validate_importer_model_type(value):
    """Validate that the given model type is supported for importing."""
    from importer.registry import supported_models

    if value not in supported_models():
        raise ValidationError(f"Unsupported model type '{value}'")


def validate_field_defaults(value):
    """Validate that the provided value is a valid dict."""
    if value is None:
        return

    if type(value) is not dict:
        # OK if we can parse it as JSON
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError(_('Value must be a valid dictionary object'))
