"""Custom validation routines for the 'importer' app."""

from django.core.exceptions import ValidationError


def validate_importer_model_type(value):
    """Validate that the given model type is supported for importing data."""
    from .models import DataImportSession

    if value not in DataImportSession.supported_models():
        raise ValidationError('Model type is not supported for importing data')
