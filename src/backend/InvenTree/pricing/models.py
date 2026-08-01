"""Database models for the 'pricing' app."""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

import InvenTree.fields

from .status_codes import CostType


class StockItemCost(models.Model):
    """Model representing a single landed-cost calculation for a StockItem.

    This is an append-only ledger - a new entry is created every time the cost
    of a StockItem is (re)calculated, rather than updating a single record in place.
    This preserves a full history of how the cost of an item has changed over time
    (e.g. as purchase invoices, duties, or freight costs are reconciled).

    Attributes:
        stock_item: The StockItem that this cost entry applies to
        part: The Part associated with the linked StockItem (denormalized for query convenience)
        cost_type: The type (source) of this cost entry
        min_cost: The minimum estimated cost for this entry
        max_cost: The maximum estimated cost for this entry
        cost: A single point-value estimate for this entry (e.g. a weighted / representative cost)
        date: Date at which this cost entry was calculated
        user: The user associated with this cost calculation (nullable, e.g. for automated calculations)
        source_data: JSON field capturing the source data used to calculate this cost
        notes: Optional notes associated with this cost entry
    """

    class Meta:
        """Meta options for the StockItemCost model."""

        verbose_name = _('Stock Item Cost')
        ordering = ['-date']

    stock_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.CASCADE,
        related_name='cost_entries',
        verbose_name=_('Stock Item'),
        help_text=_('Stock item to which this cost entry applies'),
    )

    part = models.ForeignKey(
        'part.Part',
        on_delete=models.CASCADE,
        related_name='stock_cost_entries',
        editable=False,
        verbose_name=_('Part'),
        help_text=_('Part associated with this cost entry'),
    )

    cost_type = models.PositiveIntegerField(
        default=CostType.PURCHASE.value,
        choices=CostType.items(),
        verbose_name=_('Cost Type'),
        help_text=_('Source of this cost entry'),
    )

    min_cost = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Cost'),
        help_text=_('Minimum estimated cost for this entry'),
    )

    max_cost = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Cost'),
        help_text=_('Maximum estimated cost for this entry'),
    )

    cost = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Cost'),
        help_text=_('Single point-value estimate for this entry'),
    )

    date = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        verbose_name=_('Date'),
        help_text=_('Date at which this cost entry was calculated'),
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('User'),
        help_text=_('User associated with this cost calculation'),
    )

    source_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Source Data'),
        help_text=_('Source data used to calculate this cost entry'),
    )

    notes = models.CharField(
        max_length=512,
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Notes associated with this cost entry'),
    )

    def save(self, *args, **kwargs):
        """Ensure that the 'part' link is always up to date."""
        if self.stock_item:
            self.part = self.stock_item.part

        super().save(*args, **kwargs)

    def __str__(self):
        """Return string representation of this cost entry."""
        return f'{self.stock_item} - {CostType(self.cost_type).label}'
