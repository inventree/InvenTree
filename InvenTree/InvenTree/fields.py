"""Custom fields used in InvenTree."""

import sys
from decimal import Decimal

from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from djmoney.forms.fields import MoneyField
from djmoney.models.fields import MoneyField as ModelMoneyField
from djmoney.models.validators import MinMoneyValidator
from rest_framework.fields import URLField as RestURLField
from rest_framework.fields import empty

import InvenTree.helpers

from .validators import AllowedURLValidator, allowable_url_schemes


class InvenTreeRestURLField(RestURLField):
    """Custom field for DRF with custom scheme validators."""

    def __init__(self, **kwargs):
        """Update schemes."""
        # Enforce 'max length' parameter in form validation
        if 'max_length' not in kwargs:
            kwargs['max_length'] = 200

        super().__init__(**kwargs)
        self.validators[-1].schemes = allowable_url_schemes()

    def run_validation(self, data=empty):
        """Override default validation behaviour for this field type"""

        import common.models

        strict_urls = common.models.InvenTreeSetting.get_setting(
            'INVENTREE_STRICT_URLS', True, cache=False
        )

        if not strict_urls and data is not empty:
            if '://' not in data:
                # Validate as if there were a schema provided
                data = 'http://' + data

        return super().run_validation(data=data)


class InvenTreeURLField(models.URLField):
    """Custom URL field which has custom scheme validators."""

    default_validators = [AllowedURLValidator()]

    def __init__(self, **kwargs):
        """Initialization method for InvenTreeURLField"""
        # Max length for InvenTreeURLField is set to 200
        kwargs['max_length'] = 200
        super().__init__(**kwargs)


def money_kwargs(**kwargs):
    """Returns the database settings for MoneyFields."""
    from common.settings import currency_code_default, currency_code_mappings

    # Default values (if not specified)
    if 'max_digits' not in kwargs:
        kwargs['max_digits'] = 19

    if 'decimal_places' not in kwargs:
        kwargs['decimal_places'] = 6

    if 'currency_choices' not in kwargs:
        kwargs['currency_choices'] = currency_code_mappings()

    if 'default_currency' not in kwargs:
        kwargs['default_currency'] = currency_code_default()

    return kwargs


class InvenTreeModelMoneyField(ModelMoneyField):
    """Custom MoneyField for clean migrations while using dynamic currency settings."""

    def __init__(self, **kwargs):
        """Overwrite default values and validators."""
        # detect if creating migration
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            # remove currency information for a clean migration
            kwargs['default_currency'] = ''
            kwargs['currency_choices'] = []

        kwargs = money_kwargs(**kwargs)

        # Set a minimum value validator
        validators = kwargs.get('validators', [])

        allow_negative = kwargs.pop('allow_negative', False)

        # If no validators are provided, add some "standard" ones
        if len(validators) == 0:
            if not allow_negative:
                validators.append(MinMoneyValidator(0))

        kwargs['validators'] = validators

        super().__init__(**kwargs)

    def formfield(self, **kwargs):
        """Override form class to use own function."""
        kwargs['form_class'] = InvenTreeMoneyField
        return super().formfield(**kwargs)

    def to_python(self, value):
        """Convert value to python type."""
        value = super().to_python(value)
        return round_decimal(value, self.decimal_places)

    def prepare_value(self, value):
        """Override the 'prepare_value' method, to remove trailing zeros when displaying.

        Why? It looks nice!
        """
        return round_decimal(value, self.decimal_places, normalize=True)


class InvenTreeMoneyField(MoneyField):
    """Custom MoneyField for clean migrations while using dynamic currency settings."""

    def __init__(self, *args, **kwargs):
        """Override initial values with the real info from database."""
        kwargs = money_kwargs(**kwargs)
        super().__init__(*args, **kwargs)


class DatePickerFormField(forms.DateField):
    """Custom date-picker field."""

    def __init__(self, **kwargs):
        """Set up custom values."""
        help_text = kwargs.get('help_text', _('Enter date'))
        label = kwargs.get('label', None)
        required = kwargs.get('required', False)
        initial = kwargs.get('initial', None)

        widget = forms.DateInput(attrs={'type': 'date'})

        forms.DateField.__init__(
            self,
            required=required,
            initial=initial,
            help_text=help_text,
            widget=widget,
            label=label,
        )


def round_decimal(value, places, normalize=False):
    """Round value to the specified number of places."""
    if type(value) in [Decimal, float]:
        value = round(value, places)

        if normalize:
            # Remove any trailing zeroes
            value = InvenTree.helpers.normalize(value)

    return value


class RoundingDecimalFormField(forms.DecimalField):
    """Custom FormField that automatically rounds inputs."""

    def to_python(self, value):
        """Convert value to python type."""
        value = super().to_python(value)
        return round_decimal(value, self.decimal_places)

    def prepare_value(self, value):
        """Override the 'prepare_value' method, to remove trailing zeros when displaying.

        Why? It looks nice!
        """
        return round_decimal(value, self.decimal_places, normalize=True)


class RoundingDecimalField(models.DecimalField):
    """Custom Field that automatically rounds inputs."""

    def to_python(self, value):
        """Convert value to python type."""
        value = super().to_python(value)
        return round_decimal(value, self.decimal_places)

    def formfield(self, **kwargs):
        """Return a Field instance for this field."""
        kwargs['form_class'] = RoundingDecimalFormField

        return super().formfield(**kwargs)


class InvenTreeNotesField(models.TextField):
    """Custom implementation of a 'notes' field"""

    # Maximum character limit for the various 'notes' fields
    NOTES_MAX_LENGTH = 50000

    def __init__(self, **kwargs):
        """Configure default initial values for this field"""
        kwargs['max_length'] = self.NOTES_MAX_LENGTH
        kwargs['verbose_name'] = _('Notes')
        kwargs['blank'] = True
        kwargs['null'] = True

        super().__init__(**kwargs)
