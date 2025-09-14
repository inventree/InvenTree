"""Tax configuration models for InvenTree."""

from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

import InvenTree.models
from common.currency import currency_code_default


class TaxConfiguration(InvenTree.models.InvenTreeMetadataModel):
    """Model for storing tax configuration settings.

    This model stores global tax settings that apply to all companies.
    Each configuration is tied to a specific year to track tax changes over time.

    Attributes:
        year: The year this tax configuration applies to
        name: Human-readable name for this tax configuration
        description: Optional description of the tax configuration
        rate: Tax rate as a percentage (e.g., 10.0 for 10%)
        currency: Currency for the tax configuration
        is_active: Whether this configuration is currently active
        is_inclusive: Whether prices include tax (True) or exclude tax (False)
        applies_to_sales: Whether this tax applies to sales orders
        applies_to_purchases: Whether this tax applies to purchase orders
    """

    class Meta:
        """Meta options for TaxConfiguration."""

        verbose_name = _('Tax Configuration')
        verbose_name_plural = _('Tax Configurations')
        unique_together = ['year', 'is_active']
        ordering = ['-year', '-is_active']

    year = models.PositiveIntegerField(
        verbose_name=_('Year'),
        help_text=_('The year this tax configuration applies to'),
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Human-readable name for this tax configuration'),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Optional description of the tax configuration'),
    )

    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Tax Rate (%)'),
        help_text=_('Tax rate as a percentage (e.g., 10.00 for 10%)'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00')),
        ],
    )

    currency = models.CharField(
        max_length=3,
        verbose_name=_('Currency'),
        help_text=_('Currency for this tax configuration'),
        default=currency_code_default,
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Whether this configuration is currently active'),
    )

    is_inclusive = models.BooleanField(
        default=False,
        verbose_name=_('Tax Inclusive'),
        help_text=_('Whether prices include tax (True) or exclude tax (False)'),
    )

    applies_to_sales = models.BooleanField(
        default=True,
        verbose_name=_('Applies to Sales'),
        help_text=_('Whether this tax applies to sales orders'),
    )

    applies_to_purchases = models.BooleanField(
        default=True,
        verbose_name=_('Applies to Purchases'),
        help_text=_('Whether this tax applies to purchase orders'),
    )

    def clean(self):
        """Validate the tax configuration."""
        super().clean()

        # Ensure at least one of sales or purchases is selected
        if not self.applies_to_sales and not self.applies_to_purchases:
            raise ValidationError({
                'applies_to_sales': _('Tax must apply to at least sales or purchases'),
                'applies_to_purchases': _(
                    'Tax must apply to at least sales or purchases'
                ),
            })

        # Ensure only one active configuration per year
        if self.is_active:
            existing = TaxConfiguration.objects.filter(
                year=self.year, is_active=True
            ).exclude(pk=self.pk)

            if existing.exists():
                raise ValidationError({
                    'is_active': _(
                        'Only one active tax configuration is allowed per year'
                    )
                })

    def __str__(self):
        """String representation of the tax configuration."""
        return f'{self.name} ({self.year}) - {self.rate}%'

    @classmethod
    def get_current_tax_config(cls) -> Optional['TaxConfiguration']:
        """Get the current active tax configuration for the current year."""
        from datetime import datetime

        current_year = datetime.now().year

        return cls.objects.filter(year=current_year, is_active=True).first()

    @classmethod
    def get_tax_config_for_year(cls, year: int) -> Optional['TaxConfiguration']:
        """Get the active tax configuration for a specific year."""
        return cls.objects.filter(year=year, is_active=True).first()

    def calculate_tax_amount(self, base_amount: Decimal) -> Decimal:
        """Calculate the tax amount for a given base amount.

        Args:
            base_amount: The base amount to calculate tax on

        Returns:
            The calculated tax amount
        """
        if not self.is_active:
            return Decimal('0.00')

        tax_amount = (base_amount * self.rate) / Decimal('100.00')
        return tax_amount.quantize(Decimal('0.01'))

    def calculate_total_with_tax(self, base_amount: Decimal) -> Decimal:
        """Calculate the total amount including tax.

        Args:
            base_amount: The base amount to calculate tax on

        Returns:
            The total amount including tax
        """
        if not self.is_active:
            return base_amount

        tax_amount = self.calculate_tax_amount(base_amount)
        return base_amount + tax_amount

    def calculate_base_amount_from_total(self, total_amount: Decimal) -> Decimal:
        """Calculate the base amount from a total amount that includes tax.

        Args:
            total_amount: The total amount including tax

        Returns:
            The base amount excluding tax
        """
        if not self.is_active or self.rate == 0:
            return total_amount

        # Formula: base_amount = total_amount / (1 + rate/100)
        rate_factor = Decimal('1.00') + (self.rate / Decimal('100.00'))
        base_amount = total_amount / rate_factor
        return base_amount.quantize(Decimal('0.01'))
