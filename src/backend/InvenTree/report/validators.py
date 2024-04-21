"""Validators for report models."""

from django.core.exceptions import ValidationError

import report.helpers


def validate_report_model_type(value):
    """Ensure that the selected model type is valid."""
    model_options = [el[0] for el in report.helpers.report_model_options()]

    if value not in model_options:
        raise ValidationError('Not a valid model type')


def validate_filters(value, model=None):
    """Validate that the provided model filters are valid."""
    from InvenTree.helpers import validateFilterString

    return validateFilterString(value, model=model)
