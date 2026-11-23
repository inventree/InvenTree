"""Custom validation routines for the 'importer' app."""

import json

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Define maximum limits for imported file data
IMPORTER_MAX_FILE_SIZE = 32 * 1024 * 1024
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
        # OK if we can parse it as JSON - but the result must be a dict
        try:
            value = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            raise ValidationError(_('Value must be a valid dictionary object'))

        if type(value) is not dict:
            raise ValidationError(_('Value must be a valid dictionary object'))


def validate_field_filters(value):
    """Validate the provided field filters.

    Field filters are applied as ORM filters against the related model for each field,
    so they are restricted to simple equality lookups against fields on that model:

    - Must be a dict of {field_name: {filter_key: filter_value}}
    - Filter keys cannot contain '__' (prevents traversal of related models and lookup expressions)
    - Filter keys cannot start with '_' (prevents injection of Q object arguments e.g. '_negated')
    - Filter values must be simple scalar values
    """
    if value is None:
        return

    if type(value) is not dict:
        raise ValidationError(_('Value must be a valid dictionary object'))

    for field_name, filters in value.items():
        if type(filters) is not dict:
            raise ValidationError(
                _('Filters for field {field} must be a valid dictionary object').format(
                    field=field_name
                )
            )

        for key, filter_value in filters.items():
            if (
                type(key) is not str
                or not key.isidentifier()
                or key.startswith('_')
                or '__' in key
            ):
                raise ValidationError(
                    _('Invalid filter key for field {field}: {key}').format(
                        field=field_name, key=key
                    )
                )

            if filter_value is not None and type(filter_value) not in [
                str,
                int,
                float,
                bool,
            ]:
                raise ValidationError(
                    _('Invalid filter value for field {field}: {key}').format(
                        field=field_name, key=key
                    )
                )
