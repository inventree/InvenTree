"""Validators for pricing app."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from common.settings import get_global_setting


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
