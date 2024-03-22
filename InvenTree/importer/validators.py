"""Custom validation routines for the 'importer' app."""

from django.core.exceptions import ValidationError


def validate_importer_model_type(value):
    """Validate that the given model type is supported for importing."""
    from importer.registry import supported_models

    if value not in supported_models().keys():
        raise ValidationError(f"Unsupported model type '{value}'")
