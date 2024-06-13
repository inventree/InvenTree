"""Validation helpers for common models."""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from common.settings import get_global_setting


def validate_notes_model_type(value):
    """Ensure that the provided model type is valid.

    The provided value must map to a model which implements the 'InvenTreeNotesMixin'.
    """
    import InvenTree.helpers_model
    import InvenTree.models

    if not value:
        # Empty values are allowed
        return

    model_types = list(
        InvenTree.helpers_model.getModelsWithMixin(InvenTree.models.InvenTreeNotesMixin)
    )

    model_names = [model.__name__.lower() for model in model_types]

    if value.lower() not in model_names:
        raise ValidationError(f"Invalid model type '{value}'")


def validate_decimal_places_min(value):
    """Validator for PRICING_DECIMAL_PLACES_MIN setting."""
    try:
        value = int(value)
        places_max = int(get_global_setting('PRICING_DECIMAL_PLACES', create=False))
    except Exception:
        return

    if value > places_max:
        raise ValidationError(_('Minimum places cannot be greater than maximum places'))


def validate_decimal_places_max(value):
    """Validator for PRICING_DECIMAL_PLACES_MAX setting."""
    try:
        value = int(value)
        places_min = int(get_global_setting('PRICING_DECIMAL_PLACES_MIN', create=False))
    except Exception:
        return

    if value < places_min:
        raise ValidationError(_('Maximum places cannot be less than minimum places'))


def validate_email_domains(setting):
    """Validate the email domains setting."""
    if not setting.value:
        return

    domains = setting.value.split(',')
    for domain in domains:
        if not domain:
            raise ValidationError(_('An empty domain is not allowed.'))
        if not re.match(r'^@[a-zA-Z0-9\.\-_]+$', domain):
            raise ValidationError(_(f'Invalid domain name: {domain}'))
