"""
Common database model definitions.
These models are 'generic' and do not fit a particular business logic object.
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext as _
from django.core.validators import MinValueValidator, MaxValueValidator


class Currency(models.Model):
    """
    A Currency object represents a particular unit of currency.
    Each Currency has a scaling factor which relates it to the base currency.
    There must be one (and only one) currency which is selected as the base currency,
    and each other currency is calculated relative to it.

    Attributes:
        symbol: Currency symbol e.g. $
        suffix: Currency suffix e.g. AUD
        description: Long-form description e.g. "Australian Dollars"
        value: The value of this currency compared to the base currency.
        base: True if this currency is the base currency

    """

    symbol = models.CharField(max_length=10, blank=False, unique=False, help_text=_('Currency Symbol e.g. $'))

    suffix = models.CharField(max_length=10, blank=False, unique=True, help_text=_('Currency Suffix e.g. AUD'))

    description = models.CharField(max_length=100, blank=False, help_text=_('Currency Description'))

    value = models.DecimalField(default=1.0, max_digits=10, decimal_places=5, validators=[MinValueValidator(0.00001), MaxValueValidator(100000)], help_text=_('Currency Value'))

    base = models.BooleanField(default=False, help_text=_('Use this currency as the base currency'))

    class Meta:
        verbose_name_plural = 'Currencies'

    def __str__(self):
        """ Format string for currency representation """
        s = "{sym} {suf} - {desc}".format(
            sym=self.symbol,
            suf=self.suffix,
            desc=self.description
        )

        if self.base:
            s += " (Base)"
        
        else:
            s += " = {v}".format(v=self.value)

        return s

    def save(self, *args, **kwargs):
        """ Validate the model before saving

        - Ensure that there is only one base currency!
        """

        # If this currency is set as the base currency, ensure no others are
        if self.base:
            for cur in Currency.objects.filter(base=True).exclude(pk=self.pk):
                cur.base = False
                cur.save()

        # If there are no currencies set as the base currency, set this as base
        if not Currency.objects.filter(base=True).exists():
            self.base = True

        # If this is the base currency, ensure value is set to unity
        if self.base:
            self.value = 1.0

        super().save(*args, **kwargs)
