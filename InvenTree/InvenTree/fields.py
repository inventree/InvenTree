""" Custom fields used in InvenTree """

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .validators import allowable_url_schemes

from django.forms.fields import URLField as FormURLField
from django.db import models as models
from django.core import validators
from django import forms
from decimal import Decimal

import InvenTree.helpers


class InvenTreeURLFormField(FormURLField):
    """ Custom URL form field with custom scheme validators """

    default_validators = [validators.URLValidator(schemes=allowable_url_schemes())]


class InvenTreeURLField(models.URLField):
    """ Custom URL field which has custom scheme validators """

    default_validators = [validators.URLValidator(schemes=allowable_url_schemes())]

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': InvenTreeURLFormField
        })


def round_decimal(value, places):
    """
    Round value to the specified number of places.
    """

    if value is not None:
        # see https://docs.python.org/2/library/decimal.html#decimal.Decimal.quantize for options
        return value.quantize(Decimal(10) ** -places)
    return value


class RoundingDecimalFormField(forms.DecimalField):
    def to_python(self, value):
        value = super(RoundingDecimalFormField, self).to_python(value)
        value = round_decimal(value, self.decimal_places)
        return value

    def prepare_value(self, value):
        """
        Override the 'prepare_value' method, to remove trailing zeros when displaying.
        Why? It looks nice!
        """

        if type(value) == Decimal:
            return InvenTree.helpers.normalize(value)
        else:
            return value


class RoundingDecimalField(models.DecimalField):
    def to_python(self, value):
        value = super(RoundingDecimalField, self).to_python(value)
        return round_decimal(value, self.decimal_places)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': RoundingDecimalFormField
        }

        defaults.update(kwargs)
        
        return super().formfield(**kwargs)
