"""Database models for the 'pricing' app."""

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

import structlog
from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money

import InvenTree.fields
import InvenTree.ready
import stock.models
from common.currency import currency_code_default

from .status_codes import CostType

logger = structlog.get_logger('inventree')


class StockItemCostEntry(models.Model):
    """Model representing a single cost contribution towards a StockItem.

    Only the latest entry is kept per (stock_item, cost_type) pair - recalculating
    a cost updates the existing entry in place, rather than appending a new one.
    Historical cost tracking may be added later, but is out of scope for now.

    All cost entries for a given StockItem are summed to produce the cached
    total in StockItemCost - see that model for details.

    Attributes:
        stock_item: The StockItem that this cost entry applies to
        cost_type: The type (source) of this cost entry
        min_cost: The minimum estimated cost for this entry
        max_cost: The maximum estimated cost for this entry
        date: Date at which this cost entry was last updated
        user: The user associated with this cost calculation (nullable, e.g. for automated calculations)
        source_data: JSON field capturing the source data used to calculate this cost
        notes: Optional notes associated with this cost entry
    """

    class Meta:
        """Meta options for the StockItemCostEntry model."""

        verbose_name = _('Stock Item Cost Entry')
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['stock_item', 'cost_type'], name='unique_stock_item_cost_type'
            )
        ]

    stock_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.CASCADE,
        related_name='cost_entries',
        verbose_name=_('Stock Item'),
        help_text=_('Stock item to which this cost entry applies'),
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

    date = models.DateTimeField(
        auto_now=True,
        editable=False,
        verbose_name=_('Date'),
        help_text=_('Date at which this cost entry was last updated'),
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


class StockItemCost(models.Model):
    """Cached summary of the total unit cost of a StockItem.

    This is automatically (re)calculated as the sum of all associated
    StockItemCostEntry records, whenever one of those entries is created,
    updated, or deleted (see the signals at the bottom of this file).

    This model should not be edited directly - it exists purely as a
    read-optimized cache, so that e.g. stock tables can display a total cost
    for each row without needing to sum cost entries on every request.

    Attributes:
        stock_item: The StockItem that this cost summary applies to (one-to-one)
        min_cost: The sum of all associated StockItemCostEntry.min_cost values
        max_cost: The sum of all associated StockItemCostEntry.max_cost values
        date: Date at which this summary was last calculated
    """

    class Meta:
        """Meta options for the StockItemCost model."""

        verbose_name = _('Stock Item Cost')

    stock_item = models.OneToOneField(
        'stock.StockItem',
        on_delete=models.CASCADE,
        related_name='cost',
        verbose_name=_('Stock Item'),
        help_text=_('Stock item to which this cost summary applies'),
    )

    min_cost = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Cost'),
        help_text=_('Minimum total cost, calculated from all associated cost entries'),
    )

    max_cost = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Cost'),
        help_text=_('Maximum total cost, calculated from all associated cost entries'),
    )

    date = models.DateTimeField(
        auto_now=True,
        editable=False,
        verbose_name=_('Date'),
        help_text=_('Date at which this cost summary was last calculated'),
    )

    def convert(self, money):
        """Convert a money value into the default currency.

        If no exchange rate is available, the error is logged and None is
        returned, rather than allowing the calculation to fail outright.
        """
        if money is None:
            return None

        target_currency = currency_code_default()

        try:
            return convert_money(money, target_currency)
        except MissingRate:
            logger.warning(
                'No currency conversion rate available for %s -> %s',
                money.currency,
                target_currency,
            )
            return None

    def update_cost(self, save=True):
        """Recalculate min_cost / max_cost as the sum of all cost entries."""
        currency_code = currency_code_default()

        cumulative_min = Money(0, currency_code)
        cumulative_max = Money(0, currency_code)

        any_min = False
        any_max = False

        for entry in self.stock_item.cost_entries.all():
            converted_min = self.convert(entry.min_cost)

            if converted_min is not None:
                cumulative_min += converted_min
                any_min = True

            converted_max = self.convert(entry.max_cost)

            if converted_max is not None:
                cumulative_max += converted_max
                any_max = True

        self.min_cost = cumulative_min if any_min else None
        self.max_cost = cumulative_max if any_max else None

        if save:
            self.save()

    @classmethod
    def update_for_stock_item(cls, stock_item):
        """(Re)calculate the cached cost summary for the provided StockItem.

        If the stock item has no associated cost entries, any existing
        summary is removed entirely, rather than being left around as a
        stale zero-value entry.
        """
        if not stock_item.cost_entries.exists():
            cls.objects.filter(stock_item=stock_item).delete()
            return

        instance, _created = cls.objects.get_or_create(stock_item=stock_item)
        instance.update_cost()


@receiver(
    post_save,
    sender=StockItemCostEntry,
    dispatch_uid='update_stock_item_cost_after_entry_save',
)
def update_stock_item_cost_after_entry_save(sender, instance, **kwargs):
    """Recalculate the cached StockItemCost summary when a cost entry is saved."""
    if InvenTree.ready.isImportingData():
        return

    StockItemCost.update_for_stock_item(instance.stock_item)


@receiver(
    post_delete,
    sender=StockItemCostEntry,
    dispatch_uid='update_stock_item_cost_after_entry_delete',
)
def update_stock_item_cost_after_entry_delete(sender, instance, **kwargs):
    """Recalculate the cached StockItemCost summary when a cost entry is deleted."""
    if InvenTree.ready.isImportingData():
        return

    try:
        stock_item = instance.stock_item
    except stock.models.StockItem.DoesNotExist:
        # The stock item itself may have already been removed (cascade delete)
        return

    StockItemCost.update_for_stock_item(stock_item)
