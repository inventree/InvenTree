"""Validators for generic state management."""

from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.utils.translation import gettext_lazy as _


class CustomStatusCodeValidator(BaseValidator):
    """Custom validator class for checking that a provided status code is valid."""

    def __init__(self, *args, **kwargs):
        """Initialize the validator."""
        self.status_class = kwargs.pop('status_class', None)
        super().__init__(limit_value=None, **kwargs)

    def __call__(self, value):
        """Check that the provided status code is valid."""
        if status_class := self.status_class:
            values = status_class.keys(custom=True)
            if value not in values:
                raise ValidationError(_('Invalid status code'))
