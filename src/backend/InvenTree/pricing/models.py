"""Database models for the 'pricing' app."""

from django.contrib.auth import get_user_model
from django.db import models, transaction
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


def convert_to_default_currency(money):
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


class StockItemCostEntryManager(models.Manager):
    """Manager providing helpers for assigning cost data to a StockItem.

    This is the common entry point that other apps (order, stock, build, ...)
    should use whenever a StockItem is assigned a cost - rather than each call
    site hand-rolling its own StockItemCostEntry construction.

    Cost entries are purely *additive*: a StockItem may carry any number of
    entries, including several of the same cost type (e.g. freight and duty
    both recorded as LANDED costs). The cached StockItemCost summary is simply
    the sum of every entry - see that model.
    """

    def create_cost(
        self,
        stock_item,
        cost_type,
        min_cost=None,
        max_cost=None,
        min_cost_currency=None,
        max_cost_currency=None,
        user=None,
        notes='',
        source_data=None,
    ):
        """Create a new cost entry against the provided StockItem.

        The normal save()-triggered signal fires, so the cached StockItemCost
        summary is kept in sync automatically.
        """
        if min_cost_currency is None and isinstance(min_cost, Money):
            min_cost_currency = min_cost.currency

        if max_cost_currency is None and isinstance(max_cost, Money):
            max_cost_currency = max_cost.currency

        return self.create(
            stock_item=stock_item,
            cost_type=cost_type,
            min_cost=min_cost,
            min_cost_currency=min_cost_currency,
            max_cost=max_cost,
            max_cost_currency=max_cost_currency,
            user=user,
            notes=notes,
            source_data=source_data,
        )

    def bulk_create_costs(self, entries: list[dict]):
        """Create cost entries for potentially many stock items at once.

        Each dict in `entries` supports the same keys as `create_cost`
        (stock_item is required, the rest are optional).

        As bulk_create() does not call save() and therefore does not trigger the
        usual signals, the cached StockItemCost summary for every affected stock
        item is recalculated afterwards via an offloaded 'update_stock_item_cost'
        task (batched into a single bulk task-queue write, rather than one per
        stock item).
        """
        if not entries:
            return []

        objs = []
        stock_items = {}

        for data in entries:
            stock_item = data['stock_item']
            min_cost = data.get('min_cost')
            max_cost = data.get('max_cost')

            min_cost_currency = data.get('min_cost_currency')
            if min_cost_currency is None and isinstance(min_cost, Money):
                min_cost_currency = min_cost.currency

            max_cost_currency = data.get('max_cost_currency')
            if max_cost_currency is None and isinstance(max_cost, Money):
                max_cost_currency = max_cost.currency

            objs.append(
                self.model(
                    stock_item=stock_item,
                    cost_type=data.get('cost_type', CostType.PURCHASE.value),
                    min_cost=min_cost,
                    min_cost_currency=min_cost_currency,
                    max_cost=max_cost,
                    max_cost_currency=max_cost_currency,
                    user=data.get('user'),
                    notes=data.get('notes', ''),
                    source_data=data.get('source_data'),
                )
            )

            stock_items[stock_item.pk] = stock_item

        created = self.bulk_create(objs, batch_size=500)

        self._schedule_summary_updates(stock_items.values())

        return created

    def bulk_copy_costs(self, item_pairs):
        """Copy every cost entry from a source StockItem onto a target StockItem.

        Cost data lives in a separate table keyed by stock item, so (unlike a
        plain model field) it is *not* carried across when a StockItem is
        duplicated by nulling-out its primary key. Any operation which splits
        one stock item into another must therefore copy the cost entries
        across explicitly - see StockItem.splitStock(), StockItem.serializeStock(),
        Build.complete_allocations() and SalesOrderShipment.complete_allocations().

        Costs are recorded *per unit*, so a split copies them verbatim: splitting
        changes the quantity of an item, never its unit cost. Currency, user,
        notes and source_data are preserved too, so the provenance of the
        original cost survives onto the split-off item.

        Targets are expected to be newly-created stock items with no cost data of
        their own. Copied entries are *added* to any the target already has,
        consistent with the additive behaviour of this model.

        Arguments:
            item_pairs: Iterable of (source, target) StockItem tuples. Both must
                already be saved to the database (i.e. have a primary key).

        Returns:
            The list of newly created StockItemCostEntry objects.
        """
        pairs = [(source, target) for source, target in item_pairs if source and target]

        if not pairs:
            return []

        source_ids = {source.pk for source, _target in pairs}

        # Fetch every cost entry for every source item in a single query
        entries_by_source = {}

        for entry in self.filter(stock_item_id__in=source_ids):
            entries_by_source.setdefault(entry.stock_item_id, []).append(entry)

        if not entries_by_source:
            return []

        # Existing cached summaries for the source items - a split-off item ends up
        # with exactly the same totals as its parent, so these can be copied across
        # verbatim rather than recalculated from scratch
        summaries_by_source = {
            summary.stock_item_id: summary
            for summary in StockItemCost.objects.filter(stock_item_id__in=source_ids)
        }

        objs = []
        summary_objs = []
        recalculate = []

        for source, target in pairs:
            entries = entries_by_source.get(source.pk)

            if not entries:
                continue

            for entry in entries:
                objs.append(
                    self.model(
                        stock_item=target,
                        cost_type=entry.cost_type,
                        min_cost=entry.min_cost,
                        min_cost_currency=entry.min_cost_currency,
                        max_cost=entry.max_cost,
                        max_cost_currency=entry.max_cost_currency,
                        user=entry.user,
                        notes=entry.notes,
                        source_data=entry.source_data,
                    )
                )

            if summary := summaries_by_source.get(source.pk):
                summary_objs.append(
                    StockItemCost(
                        stock_item=target,
                        min_cost=summary.min_cost,
                        min_cost_currency=summary.min_cost_currency,
                        max_cost=summary.max_cost,
                        max_cost_currency=summary.max_cost_currency,
                    )
                )
            else:
                # The source has cost entries but no cached summary yet (e.g. a
                # bulk_create_costs() recalculation is still queued) - there is nothing
                # to copy, so the target's summary must be calculated as normal
                recalculate.append(target)

        if not objs:
            return []

        with transaction.atomic():
            created = self.bulk_create(objs, batch_size=500)

            if summary_objs:
                # StockItemCost is a one-to-one cache, so any summary the targets
                # already had must be removed before the copied one is inserted
                StockItemCost.objects.filter(
                    stock_item_id__in=[obj.stock_item_id for obj in summary_objs]
                ).delete()

                StockItemCost.objects.bulk_create(summary_objs, batch_size=500)

        self._schedule_summary_updates(recalculate)

        return created

    def _schedule_summary_updates(self, stock_items):
        """Offload a cached-summary recalculation for each of the provided stock items.

        Required after any bulk_create(), which does not fire the post_save signal
        that normally keeps StockItemCost in sync.
        """
        stock_items = list(stock_items)

        if not stock_items:
            return

        # Deferred imports to avoid a circular import (pricing.models <-> pricing.tasks)
        import pricing.tasks
        from InvenTree.tasks import batch_offload_tasks, offload_task

        with batch_offload_tasks():
            for stock_item in stock_items:
                offload_task(
                    pricing.tasks.update_stock_item_cost, stock_item, group='pricing'
                )


class StockItemCostEntry(models.Model):
    """Model representing a single cost contribution towards a StockItem.

    A StockItem may carry any number of cost entries, including several of the
    same cost type - e.g. freight and duty both recorded as separate LANDED
    costs, or a build order's tracked and pooled material contributions both
    recorded as MATERIAL. Entries are never merged or replaced implicitly.

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

    objects = StockItemCostEntryManager()

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
        return convert_to_default_currency(money)

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
