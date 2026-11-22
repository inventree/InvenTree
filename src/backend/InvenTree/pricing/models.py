"""Database model definitions for the 'pricing' app."""

import collections
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connections, models, transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.signals import post_delete, post_save
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money

import common.currency
import common.models
import InvenTree.fields
import InvenTree.helpers
import InvenTree.models
import InvenTree.ready
import InvenTree.tasks
from common.currency import currency_code_default
from common.settings import get_global_setting
from InvenTree import validators
from InvenTree.cache import get_session_cache, set_session_cache
from InvenTree.exceptions import log_error
from order import models as OrderModels
from order.status_codes import PurchaseOrderStatus, SalesOrderStatusGroups
from part.models import Part

from .status_codes import CostType

logger = structlog.get_logger('inventree')


class PartPricing(InvenTree.models.InvenTreeAuditMixin, common.models.MetaMixin):
    """Model for caching min/max pricing information for a particular Part.

    It is prohibitively expensive to calculate min/max pricing for a part "on the fly".
    As min/max pricing does not change very often, we pre-calculate and cache these values.

    Whenever pricing is updated, these values are re-calculated and stored.

    Pricing information is cached for:

    - BOM cost (min / max cost of component items)
    - Purchase cost (based on purchase history)
    - Internal cost (based on user-specified InternalPriceBreak data)
    - Supplier price (based on supplier part data)
    - Variant price (min / max cost of any variants)
    - Overall best / worst (based on the values listed above)
    - Sale price break min / max values
    - Historical sale pricing min / max values

    Note that this pricing information does not take "quantity" into account:
    - This provides a simple min / max pricing range, which is quite valuable in a lot of situations
    - Quantity pricing still needs to be calculated
    - Quantity pricing can be viewed from the part detail page
    - Detailed pricing information is very context specific in any case
    """

    # Pricing is recalculated automatically (in the background) - only the
    # user-specified override values are recorded in the audit log
    AUDIT_INCLUDE_FIELDS = (
        'override_min',
        'override_min_currency',
        'override_max',
        'override_max_currency',
    )

    # Changes to the pricing overrides are included in the history of the part
    AUDIT_PARENT_FIELD = 'part'

    class Meta:
        """Metaclass providing extra model definition."""

        # Table name retained from when this model was part of the 'part' app
        db_table = 'part_partpricing'

    # When calculating assembly pricing, we limit the depth of the calculation
    MAX_PRICING_DEPTH = 50

    def __str__(self):
        """Return a string representation of this PartPricing instance."""
        return _('{part} pricing').format(part=self.part)

    @property
    def is_valid(self):
        """Return True if the cached pricing is valid."""
        return self.updated is not None

    def get_part(self):
        """Return the Part instance associated with this pricing object.

        If the part does not exist (i.e. has been deleted), return None.
        """
        try:
            part = self.part
            part.refresh_from_db()
            return part
        except (Part.DoesNotExist, IntegrityError):
            return None

    def convert(self, money):
        """Attempt to convert money value to default currency.

        If a MissingRate error is raised, ignore it and return None
        """
        if money is None:
            return None

        target_currency = currency_code_default()

        try:
            result = convert_money(money, target_currency)
        except MissingRate:
            logger.warning(
                'No currency conversion rate available for %s -> %s',
                money.currency,
                target_currency,
            )
            result = None

        return result

    def schedule_for_update(self, counter: int = 0, refresh: bool = True):
        """Schedule this pricing to be updated.

        Arguments:
            counter: Recursion counter (used to prevent infinite recursion)
            refresh: If specified, the PartPricing object will be refreshed from the database

        Note:
            Within a single request, repeated calls for the same part are cheap: a request-scoped
            cache (see InvenTree.cache) short-circuits everything below after the first call,
            avoiding redundant refresh_from_db() / existence-check queries for a part whose pricing
            has already been resolved (scheduled or not) earlier in the same request. This does not
            change behavior outside of a request (e.g. background tasks), where the cache is a
            no-op and every call runs in full.
        """
        cache_key = f'part-pricing-scheduled-{self.part_id}'
        if get_session_cache(cache_key):
            return

        try:
            self._schedule_for_update(counter=counter, refresh=refresh)
        finally:
            set_session_cache(cache_key, True)

    def _schedule_for_update(self, counter: int = 0, refresh: bool = True):
        """Implementation of schedule_for_update(), without the request-scoped cache guard."""
        # If importing data, skip pricing update
        if InvenTree.ready.isImportingData():
            return

        # If running data migrations, skip pricing update
        if InvenTree.ready.isRunningMigrations():
            return

        _part = self.get_part()

        if not _part:
            logger.warning(
                'Referenced part instance does not exist - skipping pricing update.'
            )
            return

        try:
            if refresh and self.pk:
                self.refresh_from_db()
        except (PartPricing.DoesNotExist, IntegrityError):
            # Error thrown if this PartPricing instance has already been removed
            logger.warning("Error refreshing PartPricing instance for part '%s'", _part)
            return

        # Ensure that the referenced part still exists in the database
        try:
            _part.refresh_from_db()
        except IntegrityError:
            logger.exception(
                "Could not update PartPricing as Part '%s' does not exist", _part
            )
            return

        if self.scheduled_for_update:
            # Ignore if the pricing is already scheduled to be updated
            logger.debug(
                'Pricing for %s already scheduled for update - skipping', _part
            )
            return

        if counter > self.MAX_PRICING_DEPTH:
            # Prevent infinite recursion / stack depth issues
            logger.debug(
                'Skipping pricing update for %s - maximum depth exceeded (%s)',
                _part,
                counter,
            )
            return

        try:
            self.scheduled_for_update = True
            self.save()
        except IntegrityError:
            # An IntegrityError here likely indicates that the referenced part has already been deleted
            logger.exception(
                "Could not save PartPricing for part '%s' to the database", _part
            )
            return

        import part.tasks as part_tasks

        # Pricing calculations are performed in the background,
        # unless the TESTING_PRICING flag is set
        background = not settings.TESTING or not settings.TESTING_PRICING

        # Offload task to update the pricing
        # Force async, to prevent running in the foreground (unless in testing mode)
        InvenTree.tasks.offload_task(
            part_tasks.update_part_pricing,
            self,
            counter=counter,
            force_async=background,
            group='pricing',
        )

    def update_pricing(
        self,
        counter: int = 0,
        cascade: bool = True,
        previous_min=None,
        previous_max=None,
    ):
        """Recalculate all cost data for the referenced Part instance.

        Arguments:
            counter: Recursion counter (used to prevent infinite recursion)
            cascade: If True, update pricing for all assemblies and templates which use this part
            previous_min: Previous minimum price (used to prevent further updates if unchanged)
            previous_max: Previous maximum price (used to prevent further updates if unchanged)

        """
        # If importing data, skip pricing update
        if InvenTree.ready.isImportingData():
            return

        # If running data migrations, skip pricing update
        if InvenTree.ready.isRunningMigrations():
            return

        if self.pk is not None:
            try:
                self.refresh_from_db()
            except PartPricing.DoesNotExist:
                # The underlying Part (and this pricing entry) has been deleted
                # since this update was scheduled - nothing to do
                return

        self.update_bom_cost(save=False)
        self.update_purchase_cost(save=False)
        self.update_internal_cost(save=False)
        self.update_supplier_cost(save=False)
        self.update_variant_cost(save=False)
        self.update_sale_cost(save=False)

        # Clear scheduling flag
        self.scheduled_for_update = False

        # Note: save method calls update_overall_cost
        try:
            self.save()
        except IntegrityError:
            # Background worker processes may try to concurrently update
            pass

        pricing_changed = False

        # Without previous pricing data, we assume that the pricing has changed
        if previous_min != self.overall_min or previous_max != self.overall_max:
            pricing_changed = True

        # Update parent assemblies and templates
        if pricing_changed and cascade:
            self.update_assemblies(counter)
            self.update_templates(counter)

    def update_assemblies(self, counter: int = 0):
        """Schedule updates for any assemblies which use this part."""
        # If the linked Part is used in any assemblies, schedule a pricing update for those assemblies

        if not (_part := self.get_part()):
            return

        used_in_parts = _part.get_used_in()

        for p in used_in_parts:
            p.pricing.schedule_for_update(counter=counter + 1)

    def update_templates(self, counter: int = 0):
        """Schedule updates for any template parts above this part."""
        if not (_part := self.get_part()):
            return

        templates = _part.get_ancestors(include_self=False)

        for p in templates:
            p.pricing.schedule_for_update(counter=counter + 1)

    def save(self, *args, **kwargs):
        """Whenever pricing model is saved, automatically update overall prices."""
        # Update the currency which was used to perform the calculation
        self.currency = currency_code_default()

        if not (_part := self.get_part()):
            return

        try:
            self.update_overall_cost()
            super().save(*args, **kwargs)
        except Exception:
            log_error('PartPricing.save')
            logger.error(
                "Could not save PartPricing for part '%s' to the database", _part
            )

    def update_bom_cost(self, save=True):
        """Recalculate BOM cost for the referenced Part instance.

        Iterate through the Bill of Materials, and calculate cumulative pricing:

        cumulative_min: The sum of minimum costs for each line in the BOM
        cumulative_max: The sum of maximum costs for each line in the BOM

        Note: The cumulative costs are calculated based on the specified default currency
        """
        if not (_part := self.get_part()):
            return

        if not _part.assembly:
            # Not an assembly - no BOM pricing
            self.bom_cost_min = None
            self.bom_cost_max = None

            if save:
                self.save()

            # Short circuit - no further operations required
            return

        currency_code = common.currency.currency_code_default()

        cumulative_min = Money(0, currency_code)
        cumulative_max = Money(0, currency_code)

        any_min_elements = False
        any_max_elements = False

        for bom_item in _part.get_bom_items():
            # Loop through each BOM item which is used to assemble this part

            bom_item_min = None
            bom_item_max = None

            for sub_part in bom_item.get_valid_parts_for_allocation():
                # Check each part which *could* be used

                if sub_part != bom_item.sub_part and not sub_part.active:
                    continue

                sub_part_pricing = sub_part.pricing

                sub_part_min = self.convert(sub_part_pricing.overall_min)
                sub_part_max = self.convert(sub_part_pricing.overall_max)

                if sub_part_min is not None:
                    if bom_item_min is None or sub_part_min < bom_item_min:
                        bom_item_min = sub_part_min

                if sub_part_max is not None:
                    if bom_item_max is None or sub_part_max > bom_item_max:
                        bom_item_max = sub_part_max

            # Update cumulative totals
            if bom_item_min is not None:
                bom_item_min *= bom_item.unit_quantity
                cumulative_min += self.convert(bom_item_min)

                any_min_elements = True

            if bom_item_max is not None:
                bom_item_max *= bom_item.unit_quantity
                cumulative_max += self.convert(bom_item_max)

                any_max_elements = True

        if any_min_elements:
            self.bom_cost_min = cumulative_min
        else:
            self.bom_cost_min = None

        if any_max_elements:
            self.bom_cost_max = cumulative_max
        else:
            self.bom_cost_max = None

        if save:
            self.save()

    def update_purchase_cost(self, save=True):
        """Recalculate historical purchase cost for the referenced Part instance.

        Purchase history only takes into account "completed" purchase orders.
        """
        if not (_part := self.get_part()):
            return

        # Find all line items for completed orders which reference this part
        line_items = OrderModels.PurchaseOrderLineItem.objects.filter(
            order__status=PurchaseOrderStatus.COMPLETE.value,
            received__gt=0,
            part__part=_part,
        )

        # Exclude line items which do not have an associated price
        line_items = line_items.exclude(purchase_price=None)

        purchase_min = None
        purchase_max = None

        for line in line_items:
            if line.purchase_price is None:
                continue

            # Take supplier part pack size into account
            purchase_cost = self.convert(
                line.purchase_price / line.part.pack_quantity_native
            )

            if purchase_cost is None:
                continue

            if purchase_min is None or purchase_cost < purchase_min:
                purchase_min = purchase_cost

            if purchase_max is None or purchase_cost > purchase_max:
                purchase_max = purchase_cost

        # Also include the purchase cost recorded against individual stock items
        if get_global_setting('PRICING_USE_STOCK_PRICING', True):
            for cost_min, cost_max in self.get_stock_purchase_costs():
                cost_min = self.convert(cost_min)
                cost_max = self.convert(cost_max)

                # Skip if the cost could not be converted (for some reason)
                if cost_min is None or cost_max is None:
                    continue

                if purchase_min is None or cost_min < purchase_min:
                    purchase_min = cost_min

                if purchase_max is None or cost_max > purchase_max:
                    purchase_max = cost_max

        self.purchase_cost_min = purchase_min
        self.purchase_cost_max = purchase_max

        if save:
            self.save()

    def get_stock_purchase_costs(self) -> list[tuple[Money, Money]]:
        """Return the (min, max) unit purchase cost of each stock item for this part.

        The purchase cost of a stock item is the sum of its PURCHASE cost entries
        (only - other cost types such as landed costs are excluded), using the stored
        converted values (in the default currency).

        - If PRICING_STOCK_ITEM_AGE_DAYS is set, only entries recorded (or updated)
          within that window are included
        - Stock items with any PURCHASE entry which has not been converted to the
          default currency are skipped, rather than reporting a partial cost
        """
        if not (_part := self.get_part()):
            return []

        currency = currency_code_default()

        entries = StockItemCostEntry.objects.filter(
            stock_item__part=_part, cost_type=CostType.PURCHASE
        )

        # Limit to cost entries recorded within a certain window
        days = int(get_global_setting('PRICING_STOCK_ITEM_AGE_DAYS', 0))

        if days > 0:
            date_threshold = InvenTree.helpers.current_date() - timedelta(days=days)
            entries = entries.filter(date__date__gte=date_threshold)

        valid = Q(
            converted_currency=currency,
            converted_min_cost__isnull=False,
            converted_max_cost__isnull=False,
        )

        totals = (
            entries
            .order_by()
            .values('stock_item_id')
            .annotate(
                min_total=Sum('converted_min_cost', filter=valid),
                max_total=Sum('converted_max_cost', filter=valid),
                entry_count=Count('pk'),
                valid_count=Count('pk', filter=valid),
            )
            .filter(entry_count=F('valid_count'))
        )

        return [
            (Money(row['min_total'], currency), Money(row['max_total'], currency))
            for row in totals
        ]

    def update_internal_cost(self, save=True):
        """Recalculate internal cost for the referenced Part instance."""
        if not (_part := self.get_part()):
            return

        min_int_cost = None
        max_int_cost = None

        if get_global_setting('PART_INTERNAL_PRICE', False):
            # Only calculate internal pricing if internal pricing is enabled
            for pb in _part.internalpricebreaks.all():
                cost = self.convert(pb.price)

                if cost is None:
                    # Ignore if cost could not be converted for some reason
                    continue

                if min_int_cost is None or cost < min_int_cost:
                    min_int_cost = cost

                if max_int_cost is None or cost > max_int_cost:
                    max_int_cost = cost

        self.internal_cost_min = min_int_cost
        self.internal_cost_max = max_int_cost

        if save:
            self.save()

    def update_supplier_cost(self, save=True):
        """Recalculate supplier cost for the referenced Part instance.

        - The limits are simply the lower and upper bounds of available SupplierPriceBreaks
        - We do not take "quantity" into account here
        """
        if not (_part := self.get_part()):
            return

        min_sup_cost = None
        max_sup_cost = None

        if _part.purchaseable:
            # Iterate through each available SupplierPart instance
            for sp in _part.supplier_parts.all():
                # Iterate through each available SupplierPriceBreak instance
                for pb in sp.pricebreaks.all():
                    if pb.price is None:
                        continue

                    # Ensure we take supplier part pack size into account
                    cost = self.convert(pb.price / sp.pack_quantity_native)

                    if cost is None:
                        continue

                    if min_sup_cost is None or cost < min_sup_cost:
                        min_sup_cost = cost

                    if max_sup_cost is None or cost > max_sup_cost:
                        max_sup_cost = cost

        self.supplier_price_min = min_sup_cost
        self.supplier_price_max = max_sup_cost

        if save:
            self.save()

    def update_variant_cost(self, save=True):
        """Update variant cost values.

        Here we track the min/max costs of any variant parts.
        """
        if not (_part := self.get_part()):
            return

        variant_min = None
        variant_max = None

        active_only = get_global_setting('PRICING_ACTIVE_VARIANTS', False)

        if _part.is_template:
            variants = _part.get_descendants(include_self=False)

            for v in variants:
                if active_only and not v.active:
                    # Ignore inactive variant parts
                    continue

                v_min = self.convert(v.pricing.overall_min)
                v_max = self.convert(v.pricing.overall_max)

                if v_min is not None:
                    if variant_min is None or v_min < variant_min:
                        variant_min = v_min

                if v_max is not None:
                    if variant_max is None or v_max > variant_max:
                        variant_max = v_max

        self.variant_cost_min = variant_min
        self.variant_cost_max = variant_max

        if save:
            self.save()

    def update_overall_cost(self):
        """Update overall cost values.

        Here we simply take the minimum / maximum values of the other calculated fields.
        """
        overall_min = None
        overall_max = None

        min_costs = [self.bom_cost_min, self.purchase_cost_min, self.internal_cost_min]

        max_costs = [self.bom_cost_max, self.purchase_cost_max, self.internal_cost_max]

        purchase_history_override = get_global_setting(
            'PRICING_PURCHASE_HISTORY_OVERRIDES_SUPPLIER', False
        )

        if get_global_setting('PRICING_USE_SUPPLIER_PRICING', True):
            # Add supplier pricing data, *unless* historical pricing information should override
            if self.purchase_cost_min is None or not purchase_history_override:
                min_costs.append(self.supplier_price_min)

            if self.purchase_cost_max is None or not purchase_history_override:
                max_costs.append(self.supplier_price_max)

        if get_global_setting('PRICING_USE_VARIANT_PRICING', True):
            # Include variant pricing in overall calculations
            min_costs.append(self.variant_cost_min)
            max_costs.append(self.variant_cost_max)

        # Calculate overall minimum cost
        for cost in min_costs:
            if cost is None:
                continue

            # Ensure we are working in a common currency
            cost = self.convert(cost)

            if overall_min is None or cost < overall_min:
                overall_min = cost

        # Calculate overall maximum cost
        for cost in max_costs:
            if cost is None:
                continue

            # Ensure we are working in a common currency
            cost = self.convert(cost)

            if overall_max is None or cost > overall_max:
                overall_max = cost

        if get_global_setting('PART_BOM_USE_INTERNAL_PRICE', False):
            # Check if internal pricing should override other pricing
            if self.internal_cost_min is not None:
                overall_min = self.internal_cost_min

            if self.internal_cost_max is not None:
                overall_max = self.internal_cost_max

        if self.override_min is not None:
            overall_min = self.convert(self.override_min)

        self.overall_min = overall_min

        if self.override_max is not None:
            overall_max = self.convert(self.override_max)

        self.overall_max = overall_max

    def update_sale_cost(self, save=True):
        """Recalculate sale cost data."""
        if not (_part := self.get_part()):
            return

        # Iterate through the sell price breaks
        min_sell_price = None
        max_sell_price = None

        for pb in _part.salepricebreaks.all():
            cost = self.convert(pb.price)

            if cost is None:
                continue

            if min_sell_price is None or cost < min_sell_price:
                min_sell_price = cost

            if max_sell_price is None or cost > max_sell_price:
                max_sell_price = cost

        # Record min/max values
        self.sale_price_min = min_sell_price
        self.sale_price_max = max_sell_price

        min_sell_history = None
        max_sell_history = None

        # Calculate sale price history too
        parts = self.part.get_descendants(include_self=True)

        # Find all line items for shipped sales orders which reference this part
        line_items = OrderModels.SalesOrderLineItem.objects.filter(
            order__status__in=SalesOrderStatusGroups.COMPLETE, part__in=parts
        )

        # Exclude line items which do not have associated pricing data
        line_items = line_items.exclude(sale_price=None)

        for line in line_items:
            cost = self.convert(line.sale_price)

            if cost is None:
                continue

            if min_sell_history is None or cost < min_sell_history:
                min_sell_history = cost

            if max_sell_history is None or cost > max_sell_history:
                max_sell_history = cost

        self.sale_history_min = min_sell_history
        self.sale_history_max = max_sell_history

        if save:
            self.save()

    currency = models.CharField(
        default=currency_code_default,
        max_length=10,
        verbose_name=_('Currency'),
        help_text=_('Currency used to cache pricing calculations'),
        validators=[validators.validate_currency_code],
    )

    scheduled_for_update = models.BooleanField(default=False)

    part = models.OneToOneField(
        Part,
        on_delete=models.CASCADE,
        related_name='pricing_data',
        verbose_name=_('Part'),
    )

    bom_cost_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum BOM Cost'),
        help_text=_('Minimum cost of component parts'),
    )

    bom_cost_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum BOM Cost'),
        help_text=_('Maximum cost of component parts'),
    )

    purchase_cost_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Purchase Cost'),
        help_text=_('Minimum historical purchase cost'),
    )

    purchase_cost_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Purchase Cost'),
        help_text=_('Maximum historical purchase cost'),
    )

    internal_cost_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Internal Price'),
        help_text=_('Minimum cost based on internal price breaks'),
    )

    internal_cost_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Internal Price'),
        help_text=_('Maximum cost based on internal price breaks'),
    )

    supplier_price_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Supplier Price'),
        help_text=_('Minimum price of part from external suppliers'),
    )

    supplier_price_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Supplier Price'),
        help_text=_('Maximum price of part from external suppliers'),
    )

    variant_cost_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Variant Cost'),
        help_text=_('Calculated minimum cost of variant parts'),
    )

    variant_cost_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Variant Cost'),
        help_text=_('Calculated maximum cost of variant parts'),
    )

    override_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Cost'),
        help_text=_('Override minimum cost'),
    )

    override_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Cost'),
        help_text=_('Override maximum cost'),
    )

    overall_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Cost'),
        help_text=_('Calculated overall minimum cost'),
    )

    overall_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Cost'),
        help_text=_('Calculated overall maximum cost'),
    )

    sale_price_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Sale Price'),
        help_text=_('Minimum sale price based on price breaks'),
    )

    sale_price_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Sale Price'),
        help_text=_('Maximum sale price based on price breaks'),
    )

    sale_history_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Sale Cost'),
        help_text=_('Minimum historical sale price'),
    )

    sale_history_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Sale Cost'),
        help_text=_('Maximum historical sale price'),
    )


class PartSellPriceBreak(
    InvenTree.models.InvenTreeAuditMixin, common.models.PriceBreak
):
    """Represents a price break for selling this part."""

    # Changes to a price break are included in the history of the part
    AUDIT_PARENT_FIELD = 'part'

    class Meta:
        """Metaclass providing extra model definition."""

        verbose_name = _('Part Sale Price Break')
        unique_together = ('part', 'quantity')
        # Table name retained from when this model was part of the 'part' app
        db_table = 'part_partsellpricebreak'

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartSellPriceBreak model."""
        return reverse('api-part-sale-price-list')

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='salepricebreaks',
        limit_choices_to={'salable': True},
        verbose_name=_('Part'),
    )


class PartInternalPriceBreak(
    InvenTree.models.InvenTreeAuditMixin, common.models.PriceBreak
):
    """Represents a price break for internally selling this part."""

    # Changes to a price break are included in the history of the part
    AUDIT_PARENT_FIELD = 'part'

    class Meta:
        """Metaclass providing extra model definition."""

        unique_together = ('part', 'quantity')
        verbose_name = _('Part Internal Price Break')
        # Table name retained from when this model was part of the 'part' app
        db_table = 'part_partinternalpricebreak'

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartInternalPriceBreak model."""
        return reverse('api-part-internal-price-list')

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='internalpricebreaks',
        verbose_name=_('Part'),
    )


@receiver(
    post_save, sender=PartSellPriceBreak, dispatch_uid='post_save_sale_price_break'
)
@receiver(
    post_save,
    sender=PartInternalPriceBreak,
    dispatch_uid='post_save_internal_price_break',
)
def update_pricing_after_edit(sender, instance, created, **kwargs):
    """Callback function when a part price break is created or updated."""
    # Update part pricing *unless* we are importing data
    if (
        InvenTree.ready.canAppAccessDatabase(allow_test=settings.TESTING_PRICING)
        and not InvenTree.ready.isImportingData()
    ):
        if instance.part:
            instance.part.schedule_pricing_update(create=True)


@receiver(
    post_delete, sender=PartSellPriceBreak, dispatch_uid='post_delete_sale_price_break'
)
@receiver(
    post_delete,
    sender=PartInternalPriceBreak,
    dispatch_uid='post_delete_internal_price_break',
)
def update_pricing_after_delete(sender, instance, **kwargs):
    """Callback function when a part price break is deleted."""
    # Update part pricing *unless* we are importing data
    if (
        InvenTree.ready.canAppAccessDatabase(allow_test=settings.TESTING_PRICING)
        and not InvenTree.ready.isImportingData()
    ):
        try:
            part = instance.part
            part.schedule_pricing_update(create=False)
        except Part.DoesNotExist:
            # The part instance may have already been deleted,
            # in which case we cannot update pricing
            pass


# Precision used for all stored stock item cost values (matches the default MoneyField precision)
COST_MAX_DIGITS = 19
COST_DECIMAL_PLACES = 6

# Plugin slugs are lowercase, and may contain digits, hyphens and underscores
PLUGIN_SLUG_REGEX = re.compile(r'[a-z0-9][a-z0-9_-]*')


class CostSource:
    """Values for the StockItemCostEntry.source field - i.e. *who or what* created a cost entry.

    Naming convention:
    - Core InvenTree sources use a bare name (one of the constants below)
    - Plugins use the 'plugin:<slug>' form (see CostSource.plugin)

    Attributes:
        MANUAL: Entered manually by a user (the default for entries created via the API)
        PURCHASE_ORDER: Created when receiving items against a purchase order
        BUILD: Created when completing a build order
        MERGE: Created when merging stock items
        DISASSEMBLY: Created when disassembling a stock item
        LEGACY: Migrated from the legacy StockItem.purchase_price field
    """

    MANUAL = 'manual'
    PURCHASE_ORDER = 'purchase_order'
    BUILD = 'build'
    MERGE = 'merge'
    DISASSEMBLY = 'disassembly'
    LEGACY = 'legacy'

    CORE_SOURCES = frozenset([
        MANUAL,
        PURCHASE_ORDER,
        BUILD,
        MERGE,
        DISASSEMBLY,
        LEGACY,
    ])

    PLUGIN_PREFIX = 'plugin:'

    @classmethod
    def plugin(cls, slug: str) -> str:
        """Return the source value for cost entries created by the plugin with the given slug."""
        return f'{cls.PLUGIN_PREFIX}{slug}'

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Return True if the provided value follows the source naming convention."""
        if value in cls.CORE_SOURCES:
            return True

        if value.startswith(cls.PLUGIN_PREFIX):
            slug = value[len(cls.PLUGIN_PREFIX) :]
            return bool(PLUGIN_SLUG_REGEX.fullmatch(slug))

        return False


def validate_cost_source(value: str):
    """Validate that a cost entry source follows the naming convention (see CostSource)."""
    if value and not CostSource.is_valid(value):
        raise ValidationError(
            _("Invalid source - must be one of {sources}, or 'plugin:<slug>'").format(
                sources=', '.join(sorted(CostSource.CORE_SOURCES))
            )
        )


def convert_cost(value, currency: str, target_currency: str):
    """Convert a single cost value from one currency to another.

    Arguments:
        value: The (Decimal) value to convert
        currency: The currency code of the provided value
        target_currency: The currency code to convert to

    Returns:
        The converted value (rounded to the stored precision),
        or None if no exchange rate is available.
    """
    if value is None:
        return None

    if currency == target_currency:
        return value

    try:
        converted = convert_money(Money(value, currency), target_currency)
    except MissingRate:
        logger.warning(
            'No currency conversion rate available for %s -> %s',
            currency,
            target_currency,
        )
        return None

    return round(converted.amount, COST_DECIMAL_PLACES)


class StockItemCostEntryManager(models.Manager):
    """Manager providing helpers for assigning cost data to a StockItem.

    This is the common entry point that other apps (order, stock, build, plugins, ...)
    should use whenever a StockItem is assigned a cost. Every helper keeps the cached
    StockItemCost summary of each affected stock item up to date (synchronously).

    The `source` of a cost entry identifies who or what created it - see CostSource
    for the naming convention ('manual', 'purchase_order', ..., or 'plugin:<slug>').
    """

    COST_KEYS = ('min_cost', 'max_cost')

    def normalize_cost_data(self, data: dict, currency: Optional[str] = None) -> dict:
        """Convert any Money values in the provided data into a (currency, amount) pair.

        Arguments:
            data: Dict of StockItemCostEntry field values. min_cost / max_cost may be Money instances.
            currency: The existing currency of the entry (if any), checked against Money values
                when the data does not provide its own currency or the other cost bound

        Returns:
            A copy of the provided data, with plain Decimal cost values and the matching currency

        Raises:
            ValidationError: If the provided values have conflicting currencies
        """
        data = dict(data)

        currencies = {
            data[key].currency.code
            for key in self.COST_KEYS
            if isinstance(data.get(key), Money)
        }

        if explicit_currency := data.get('currency'):
            currencies.add(explicit_currency)

        # A single Money bound would otherwise silently change the currency of the other bound
        if (
            currency
            and 'currency' not in data
            and not all(key in data for key in self.COST_KEYS)
        ):
            currencies.add(currency)

        if len(currencies) > 1:
            raise ValidationError({
                'currency': _('Minimum and maximum cost must use the same currency')
            })

        for key in self.COST_KEYS:
            if isinstance(data.get(key), Money):
                data[key] = data[key].amount

        if currencies:
            data['currency'] = currencies.pop()

        return data

    def build_entry(self, **data):
        """Construct (but do not save) a new StockItemCostEntry instance.

        In addition to the model fields, min_cost and max_cost may be provided as
        Money instances, in which case the currency is taken from the provided value(s).

        Raises:
            ValidationError: If the provided Money values have conflicting currencies
        """
        return self.model(**self.normalize_cost_data(data))

    def create_cost(self, stock_item, cost_type, source: str, **kwargs):
        """Create (and save) a new cost entry against the provided StockItem.

        Arguments:
            stock_item: The StockItem to which the cost applies
            cost_type: The category of the cost (see CostType)
            source: Who or what created the cost entry (see CostSource)
            **kwargs: Any other StockItemCostEntry fields (see build_entry)

        Returns:
            The created StockItemCostEntry

        Raises:
            ValidationError: If the entry is not valid
        """
        entry = self.build_entry(
            stock_item=stock_item, cost_type=cost_type, source=source, **kwargs
        )
        entry.save()

        return entry

    def update_cost(self, entry, **changes):
        """Update (and save) an existing cost entry.

        Arguments:
            entry: The StockItemCostEntry to update
            **changes: The fields to change. min_cost / max_cost may be Money instances,
                in which case the entry currency is updated to match.
                A single Money bound must match the existing currency, unless the
                currency (or the other bound) is also provided.

        Returns:
            The updated StockItemCostEntry

        Raises:
            ValidationError: If the updated entry is not valid
            ValueError: If an attempt is made to move the entry to a different stock item
        """
        if {'stock_item', 'stock_item_id'} & changes.keys():
            raise ValueError('Cost entries cannot be moved to a different stock item')

        changes = self.normalize_cost_data(changes, currency=entry.currency)

        for field, value in changes.items():
            setattr(entry, field, value)

        entry.save()

        return entry

    def delete_costs(self, entries) -> int:
        """Delete cost entries, and update the cached cost summary of each affected stock item.

        Arguments:
            entries: A queryset or iterable of StockItemCostEntry instances

        Returns:
            The number of deleted entries
        """
        if not isinstance(entries, models.QuerySet):
            entries = self.filter(pk__in=[entry.pk for entry in entries])

        with transaction.atomic():
            stock_item_ids = set(
                entries.order_by().values_list('stock_item_id', flat=True).distinct()
            )

            StockItemCost.objects.lock_stock_items(stock_item_ids)

            _count, deleted = entries.delete()

            StockItemCost.objects.update_for_stock_items(stock_item_ids)

        return deleted.get(self.model._meta.label, 0)

    def bulk_create_costs(self, entries: list[dict]) -> list:
        """Create cost entries for potentially many stock items at once.

        Each dict in `entries` supports the same keys as `build_entry`
        (stock_item or stock_item_id, cost_type and source are required).

        Every entry is validated and converted before any are created (all or nothing),
        and the cached StockItemCost summary of each affected stock item
        is updated (synchronously) in the same transaction.

        Raises:
            ValidationError: If any of the entries is not valid
        """
        for data in entries:
            if not data.get('source'):
                raise ValidationError({
                    'source': _('A source must be provided for each cost entry')
                })

        objs = self.prepare_entries(entries)

        if not objs:
            return []

        stock_item_ids = {obj.stock_item_id for obj in objs}

        with transaction.atomic():
            StockItemCost.objects.lock_stock_items(stock_item_ids)
            created = self.save_prepared_entries(objs)
            StockItemCost.objects.update_for_stock_items(stock_item_ids)

        return created

    def replace_costs(
        self, stock_item, source: str, entries: list[dict], cost_type=None
    ) -> list:
        """Replace all cost entries from a given source against a StockItem.

        This is intended for business logic (or plugins) which (re)calculate a cost,
        and should replace any previous result rather than add to it.
        Existing entries from other sources are left untouched.

        Arguments:
            stock_item: The StockItem to which the costs apply
            source: Who or what created the cost entries (see CostSource)
            entries: List of dicts of StockItemCostEntry fields (see build_entry).
                The stock_item and source keys are set automatically.
                An empty list removes the existing entries.
            cost_type: If provided, only existing entries of this cost type are replaced

        Returns:
            The created StockItemCostEntry objects

        Raises:
            ValidationError: If any of the new entries is not valid (no changes are made)
        """
        objs = self.prepare_entries([
            {**data, 'stock_item': stock_item, 'source': source} for data in entries
        ])

        existing = self.filter(stock_item=stock_item, source=source)

        if cost_type is not None:
            existing = existing.filter(cost_type=cost_type)

            if any(obj.cost_type != cost_type for obj in objs):
                raise ValidationError({
                    'cost_type': _('New entries must match the replaced cost type')
                })

        with transaction.atomic():
            StockItemCost.objects.lock_stock_items([stock_item.pk])
            existing.delete()
            created = self.save_prepared_entries(objs)
            StockItemCost.objects.update_for_stock_items([stock_item.pk])

        return created

    def prepare_entries(self, entries: list[dict]) -> list:
        """Construct and validate (but do not save) new cost entries.

        Raises:
            ValidationError: If any of the entries is not valid
        """
        objs = []

        for data in entries:
            obj = self.build_entry(**data)
            obj.prepare()
            objs.append(obj)

        return objs

    def save_prepared_entries(self, objs: list) -> list:
        """Save new (prepared) cost entries, recording an audit entry for each.

        This does *not* update the cached cost summaries - the caller is responsible for that.
        """
        from audit.helpers import record_created

        if not objs:
            return []

        if connections[self.db].features.can_return_rows_from_bulk_insert:
            created = self.bulk_create(objs, batch_size=500)
            record_created(self.model, created)
            return created

        # Primary keys are not returned from bulk inserts (e.g. MySQL),
        # so the entries are saved individually (which also records the audit entries)
        for obj in objs:
            super(StockItemCostEntry, obj).save()

        return objs

    def copy_costs(self, pairs) -> list:
        """Copy all cost entries from source stock items onto target stock items.

        Used whenever a stock item is duplicated (split, serialized, partially consumed
        or shipped), so that the new stock item carries the same unit cost as its source.
        Valid because all costs are *per unit* (see StockItemCostEntry).

        Every field is copied verbatim - including the source, user,
        and the stored converted values (no reconversion takes place).
        The cached StockItemCost summary of each target stock item is then (re)calculated.

        Arguments:
            pairs: Iterable of (source, target) pairs - each either a StockItem or a primary key.
                A source may be copied onto any number of targets.

        Returns:
            The created StockItemCostEntry objects
        """
        targets = collections.defaultdict(list)

        for source, target in pairs:
            source_id = getattr(source, 'pk', source)
            target_id = getattr(target, 'pk', target)

            if source_id is None or target_id is None:
                raise ValueError(
                    'Cost entries can only be copied between saved stock items'
                )

            if source_id != target_id:
                targets[source_id].append(target_id)

        if not targets:
            return []

        fields = [
            field.attname
            for field in self.model._meta.concrete_fields
            if not field.primary_key and field.attname != 'stock_item_id'
        ]

        target_ids = {target_id for ids in targets.values() for target_id in ids}

        with transaction.atomic():
            # Lock the source items too, so that the copied entries are consistent
            StockItemCost.objects.lock_stock_items(target_ids | set(targets.keys()))

            objs = []

            for entry in (
                self
                .filter(stock_item_id__in=targets.keys())
                .order_by('pk')
                .iterator(chunk_size=500)
            ):
                data = {field: getattr(entry, field) for field in fields}

                for target_id in targets[entry.stock_item_id]:
                    objs.append(self.model(stock_item_id=target_id, **data))

            created = self.save_prepared_entries(objs)

            # Note: Targets without any copied entries are included,
            # so that any (stale) summary is removed
            StockItemCost.objects.update_for_stock_items(target_ids)

        return created

    def build_merge_entries(self, target, items) -> Optional[list]:
        """Calculate the cost entries for a stock item which is about to be merged.

        Must be called *before* the merge takes place - i.e. while all of the merged stock items
        (and their cost entries) still exist, and before any quantities change.

        One entry is calculated per cost type, as the quantity-weighted average of the per-unit
        costs of the merged stock items. The original entries are recorded in 'source_data'.

        Rules:
        - Stock items without *any* cost entries have an unknown cost, and are excluded entirely
        - A stock item without an entry of a particular cost type contributes zero for that type
        - If every entry of a cost type has the same (original) currency, the average is
          calculated in that currency. Otherwise, the stored converted values are used, and any
          entry without a converted value is excluded (and recorded in 'source_data')

        Arguments:
            target: The StockItem which the other items are being merged into
            items: All StockItems being merged (including the target)

        Returns:
            A list of dicts (see StockItemCostRecorder.add) for the merged stock item,
            or None if the cost data of the target stock item does not need to change
        """
        quantities = {item.pk: Decimal(item.quantity) for item in [target, *items]}

        queryset = self.filter(stock_item_id__in=quantities.keys())

        # Re-attempt conversion of any entries without a (current) converted value
        self.reconvert_costs(queryset)

        entries = list(queryset.order_by('pk'))

        contributing = {entry.stock_item_id for entry in entries}

        if not contributing or contributing == {target.pk}:
            # No change required to the cost data of the target stock item
            return None

        total_quantity = sum(quantities[pk] for pk in contributing)

        if total_quantity <= 0:
            return None

        default_currency = currency_code_default()

        by_type = collections.defaultdict(list)

        for entry in entries:
            by_type[entry.cost_type].append(entry)

        results = []

        for cost_type, type_entries in sorted(by_type.items()):
            currencies = {entry.currency for entry in type_entries}

            if len(currencies) == 1:
                # Average in the original currency (exact - no conversion required)
                currency = currencies.pop()
                values = [
                    (entry, entry.min_cost, entry.max_cost) for entry in type_entries
                ]
            else:
                # Use the stored converted values (if current)
                currency = default_currency
                values = [
                    (entry, entry.converted_min_cost, entry.converted_max_cost)
                    if entry.converted_currency == default_currency
                    else (entry, None, None)
                    for entry in type_entries
                ]

            min_total = Decimal(0)
            max_total = Decimal(0)
            excluded = []

            for entry, min_cost, max_cost in values:
                if min_cost is None or max_cost is None:
                    excluded.append(entry.pk)
                    continue

                quantity = quantities[entry.stock_item_id]
                min_total += min_cost * quantity
                max_total += max_cost * quantity

            if len(excluded) == len(type_entries):
                # No usable values for this cost type
                continue

            results.append({
                'cost_type': cost_type,
                'min_cost': min_total / total_quantity,
                'max_cost': max_total / total_quantity,
                'currency': currency,
                'notes': str(_('Weighted average of merged stock items')),
                'source_data': {
                    'merged_items': sorted(contributing),
                    'quantities': {
                        str(pk): str(quantities[pk]) for pk in sorted(contributing)
                    },
                    'excluded_entries': excluded,
                    'entries': [entry.snapshot() for entry in type_entries],
                },
            })

        return results

    def apply_merged_costs(self, target, entries: list, user=None) -> list:
        """Replace the cost entries of a merged stock item (see build_merge_entries).

        Arguments:
            target: The StockItem which the other items were merged into
            entries: The entries returned by build_merge_entries
            user: The user who performed the merge

        Returns:
            The created StockItemCostEntry objects
        """
        from pricing.helpers import StockItemCostRecorder

        with transaction.atomic():
            StockItemCost.objects.lock_stock_items([target.pk])

            self.filter(stock_item=target).delete()

            costs = StockItemCostRecorder(source=CostSource.MERGE, user=user)

            for data in entries:
                costs.add(target, **data)

            created = costs.save()

            # Ensure that the summary is updated, even if no entries were created
            StockItemCost.objects.update_for_stock_items([target.pk])

        return created

    def reconvert_costs(self, queryset=None) -> int:
        """Re-attempt currency conversion for entries which need it.

        This covers entries which could not be converted (no exchange rate was available),
        or which were converted to a currency which is no longer the default currency.

        The cached StockItemCost summary for every affected stock item is recalculated,
        including those whose entries still cannot be converted.

        Arguments:
            queryset: Optional queryset of entries to check (defaults to all entries)

        Returns:
            The number of entries which were successfully converted
        """
        currency = currency_code_default()

        if queryset is None:
            queryset = self.all()

        queryset = queryset.filter(
            Q(converted_min_cost__isnull=True)
            | Q(converted_max_cost__isnull=True)
            | ~Q(converted_currency=currency)
        )

        updated = []

        with transaction.atomic():
            stock_item_ids = set(
                queryset.order_by().values_list('stock_item_id', flat=True).distinct()
            )

            # Lock the affected stock items *before* reading the entries,
            # so that a concurrent edit of an entry is not overwritten with stale values
            StockItemCost.objects.lock_stock_items(stock_item_ids)

            for entry in queryset.filter(stock_item_id__in=stock_item_ids).order_by(
                'pk'
            ):
                entry.convert_costs()

                if entry.converted_currency:
                    updated.append(entry)

            self.bulk_update(
                updated,
                ['converted_currency', 'converted_min_cost', 'converted_max_cost'],
                batch_size=500,
            )

            StockItemCost.objects.update_for_stock_items(stock_item_ids)

        return len(updated)


class StockItemCostEntry(InvenTree.models.InvenTreeAuditMixin, models.Model):
    """A single cost contribution towards the unit cost of a StockItem.

    A StockItem may carry any number of cost entries, including several of the
    same cost type (e.g. freight and duty both recorded as LANDED costs).
    All cost entries for a StockItem are summed to produce the cached StockItemCost summary.

    Rules:
    - All costs are *per unit* of the stock item
    - Each entry has a single currency, which applies to both the minimum and maximum cost
    - If only one of min_cost / max_cost is provided, the other is set to the same value
    - Negative costs are allowed (e.g. rebates or credits)
    - Costs are converted to the default currency when the entry is created
      (or its costs are changed), and the converted values are stored alongside the original values

    Note: The cached StockItemCost summary is updated when an entry is saved or deleted
    via the model instance (or the manager helpers). Queryset update() / delete() operations
    bypass this, and must call StockItemCost.objects.update_for_stock_items() themselves.

    Attributes:
        stock_item: The StockItem that this cost entry applies to
        cost_type: The category of this cost entry (see CostType)
        source: Identifies who or what created this cost entry (e.g. a plugin slug)
        currency: Currency code for the min_cost and max_cost values
        min_cost: Minimum unit cost for this entry
        max_cost: Maximum unit cost for this entry
        converted_currency: Currency code for the converted values (empty if conversion failed)
        converted_min_cost: min_cost converted to the default currency
        converted_max_cost: max_cost converted to the default currency
        date: Date at which this cost entry was last updated
        user: The user associated with this cost entry (nullable, e.g. for automated calculations)
        source_data: JSON data capturing the source data used to calculate this cost
        notes: Optional notes associated with this cost entry
    """

    class Meta:
        """Meta options for the StockItemCostEntry model."""

        verbose_name = _('Stock Item Cost Entry')
        verbose_name_plural = _('Stock Item Cost Entries')

    # Cost entries are shown in the audit history of the stock item
    AUDIT_PARENT_FIELD = 'stock_item'
    AUDIT_EXCLUDE_FIELDS = ('date',)

    objects = StockItemCostEntryManager()

    def __str__(self):
        """Return a string representation of this cost entry."""
        return f'{self.get_cost_type_display()} cost ({self.source})'

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the StockItemCostEntry model."""
        return reverse('api-stock-cost-entry-list')

    @classmethod
    def from_db(cls, db, field_names, values):
        """Record the loaded cost values, so that changes can be detected on save."""
        instance = super().from_db(db, field_names, values)
        instance._loaded_costs = instance.cost_signature()
        return instance

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
        help_text=_('Category of this cost entry'),
    )

    source = models.CharField(
        max_length=100,
        default=CostSource.MANUAL,
        db_index=True,
        validators=[validate_cost_source],
        verbose_name=_('Source'),
        help_text=_(
            "Identifies who or what created this cost entry (e.g. 'manual', or 'plugin:<slug>')"
        ),
    )

    currency = models.CharField(
        default=currency_code_default,
        max_length=10,
        verbose_name=_('Currency'),
        help_text=_('Currency for the minimum and maximum cost'),
        validators=[validators.validate_currency_code],
    )

    min_cost = models.DecimalField(
        max_digits=COST_MAX_DIGITS,
        decimal_places=COST_DECIMAL_PLACES,
        null=True,
        blank=True,
        verbose_name=_('Minimum Cost'),
        help_text=_('Minimum unit cost for this entry'),
    )

    max_cost = models.DecimalField(
        max_digits=COST_MAX_DIGITS,
        decimal_places=COST_DECIMAL_PLACES,
        null=True,
        blank=True,
        verbose_name=_('Maximum Cost'),
        help_text=_('Maximum unit cost for this entry'),
    )

    converted_currency = models.CharField(
        max_length=10,
        blank=True,
        editable=False,
        verbose_name=_('Converted Currency'),
        help_text=_('Currency for the converted cost values'),
    )

    converted_min_cost = models.DecimalField(
        max_digits=COST_MAX_DIGITS,
        decimal_places=COST_DECIMAL_PLACES,
        null=True,
        blank=True,
        editable=False,
        verbose_name=_('Converted Minimum Cost'),
        help_text=_('Minimum unit cost, converted to the default currency'),
    )

    converted_max_cost = models.DecimalField(
        max_digits=COST_MAX_DIGITS,
        decimal_places=COST_DECIMAL_PLACES,
        null=True,
        blank=True,
        editable=False,
        verbose_name=_('Converted Maximum Cost'),
        help_text=_('Maximum unit cost, converted to the default currency'),
    )

    date = models.DateTimeField(
        auto_now=True,
        editable=False,
        verbose_name=_('Date'),
        help_text=_('Date at which this cost entry was last updated'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('User'),
        help_text=_('User associated with this cost entry'),
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

    @property
    def min_cost_money(self):
        """Return the minimum cost as a Money instance (or None)."""
        return to_money(self.min_cost, self.currency)

    @property
    def max_cost_money(self):
        """Return the maximum cost as a Money instance (or None)."""
        return to_money(self.max_cost, self.currency)

    def cost_signature(self) -> tuple:
        """Return the (currency, min_cost, max_cost) values which determine the converted costs.

        Values are read directly from the instance dict, to avoid loading deferred fields.
        """
        return (
            self.__dict__.get('currency'),
            self.__dict__.get('min_cost'),
            self.__dict__.get('max_cost'),
        )

    def snapshot(self) -> dict:
        """Return a JSON serializable record of this entry (e.g. to retain after it is removed)."""

        def value(val):
            return None if val is None else str(val)

        return {
            'pk': self.pk,
            'stock_item': self.stock_item_id,
            'cost_type': self.cost_type,
            'source': self.source,
            'currency': self.currency,
            'min_cost': value(self.min_cost),
            'max_cost': value(self.max_cost),
            'converted_currency': self.converted_currency,
            'converted_min_cost': value(self.converted_min_cost),
            'converted_max_cost': value(self.converted_max_cost),
            'user': self.user_id,
            'notes': self.notes,
            'source_data': self.source_data,
        }

    def clean_fields(self, exclude=None):
        """Round the cost values to the stored precision, before field validation."""
        for name in ['min_cost', 'max_cost']:
            value = getattr(self, name)

            if value is None:
                continue

            if not isinstance(value, Decimal):
                try:
                    value = Decimal(str(value))
                except InvalidOperation:
                    # Invalid value - this is reported by the field validation
                    continue

            if value.is_finite():
                setattr(self, name, round(value, COST_DECIMAL_PLACES))

        super().clean_fields(exclude=exclude)

    def clean(self):
        """Validate the cost values for this entry.

        - At least one of min_cost / max_cost must be provided
        - A missing bound is set to the same value as the provided bound
        - min_cost must not be greater than max_cost
        """
        super().clean()

        if self.min_cost is None and self.max_cost is None:
            raise ValidationError({
                'min_cost': _('A minimum or maximum cost must be provided')
            })

        if self.min_cost is None:
            self.min_cost = self.max_cost

        if self.max_cost is None:
            self.max_cost = self.min_cost

        # Values may not yet be valid numbers, if field validation has failed
        if (
            isinstance(self.min_cost, Decimal)
            and isinstance(self.max_cost, Decimal)
            and self.min_cost > self.max_cost
        ):
            raise ValidationError({
                'max_cost': _('Maximum cost must not be less than minimum cost')
            })

    def needs_conversion(self) -> bool:
        """Return True if the converted cost values need to be (re)calculated.

        This is the case if the entry is new, its cost values have changed,
        or the existing converted values are missing or not in the default currency.
        """
        if self.cost_signature() != getattr(self, '_loaded_costs', None):
            return True

        if self.converted_min_cost is None or self.converted_max_cost is None:
            return True

        return self.converted_currency != currency_code_default()

    def convert_costs(self):
        """Convert the cost values into the default currency, at the current exchange rate.

        If either value cannot be converted, both converted values are cleared.
        """
        target_currency = currency_code_default()

        converted_min = convert_cost(self.min_cost, self.currency, target_currency)
        converted_max = convert_cost(self.max_cost, self.currency, target_currency)

        if converted_min is None or converted_max is None:
            self.converted_currency = ''
            self.converted_min_cost = None
            self.converted_max_cost = None
        else:
            self.converted_currency = target_currency
            self.converted_min_cost = converted_min
            self.converted_max_cost = converted_max

    def prepare(self):
        """Validate this entry, and calculate the converted cost values (if required).

        Raises:
            ValidationError: If the entry is not valid
        """
        # Related fields are excluded, to avoid additional database queries
        self.full_clean(
            exclude=['stock_item', 'user'],
            validate_unique=False,
            validate_constraints=False,
        )

        if self.needs_conversion():
            self.convert_costs()

    def save(self, *args, **kwargs):
        """Validate and save this entry, and update the cached cost summary for the stock item."""
        self.prepare()

        with transaction.atomic():
            StockItemCost.objects.lock_stock_items([self.stock_item_id])
            super().save(*args, **kwargs)
            StockItemCost.objects.update_for_stock_items([self.stock_item_id])

        self._loaded_costs = self.cost_signature()

    def delete(self, *args, **kwargs):
        """Delete this entry, and update the cached cost summary for the stock item."""
        stock_item_id = self.stock_item_id

        with transaction.atomic():
            StockItemCost.objects.lock_stock_items([stock_item_id])
            result = super().delete(*args, **kwargs)
            StockItemCost.objects.update_for_stock_items([stock_item_id])

        return result


class StockItemCostManager(models.Manager):
    """Manager for the StockItemCost model."""

    def lock_stock_items(self, stock_item_ids):
        """Acquire a row-level lock on each of the provided stock items.

        Every operation which writes cost entries holds this lock (from *before* the
        entries are written, until the transaction completes). This serializes concurrent
        cost writes against the same stock item - otherwise two transactions could each
        calculate a summary which is missing the other's (uncommitted) entries,
        and the last one to commit would overwrite the summary with an incorrect total.

        - Rows are locked in primary key order, to avoid lock-ordering deadlocks
        - Where supported (PostgreSQL), FOR NO KEY UPDATE is used. This does not conflict
          with the KEY SHARE lock taken by inserting a row which references the stock item
          (e.g. a cost entry or tracking entry), and is compatible with existing
          FOR UPDATE locks held on the stock item by the same transaction
        - Locking is a no-op on backends which do not support row locks (e.g. SQLite,
          which serializes all writes)

        Note: Must be called from within a database transaction.

        Arguments:
            stock_item_ids: Iterable of StockItem primary keys
        """
        from stock.models import StockItem

        stock_item_ids = sorted({pk for pk in stock_item_ids if pk is not None})

        if not stock_item_ids:
            return

        no_key = connections[self.db].features.has_select_for_no_key_update

        list(
            StockItem.objects
            .using(self.db)
            .select_for_update(no_key=no_key)
            .filter(pk__in=stock_item_ids)
            .order_by('pk')
            .values_list('pk', flat=True)
        )

    def update_for_stock_items(self, stock_item_ids):
        """(Re)calculate the cached cost summary for each of the provided stock items.

        The summary is calculated from the stored converted values of each entry,
        so it is not affected by later changes to exchange rates.

        - Stock items with no cost entries have their summary removed
        - Entries without a converted value in the default currency are excluded,
          and the summary is marked as incomplete

        The stock items are locked (see lock_stock_items), and the cost entries are then
        (re)fetched with a locking read, so that the summary is calculated from the
        latest committed entries - even under REPEATABLE READ isolation (e.g. MySQL),
        where a plain read could return a stale snapshot.

        Arguments:
            stock_item_ids: Iterable of StockItem primary keys
        """
        stock_item_ids = {pk for pk in stock_item_ids if pk is not None}

        if not stock_item_ids:
            return

        currency = currency_code_default()

        with transaction.atomic(using=self.db):
            self.lock_stock_items(stock_item_ids)

            entries = (
                StockItemCostEntry.objects
                .using(self.db)
                .select_for_update()
                .filter(stock_item_id__in=stock_item_ids)
                .order_by('pk')
                .values_list(
                    'stock_item_id',
                    'converted_currency',
                    'converted_min_cost',
                    'converted_max_cost',
                )
            )

            # stock_item_id -> [min_total, max_total, entry_count, valid_count]
            totals = {}

            for pk, converted_currency, min_cost, max_cost in entries:
                row = totals.setdefault(pk, [Decimal(0), Decimal(0), 0, 0])
                row[2] += 1

                if (
                    converted_currency == currency
                    and min_cost is not None
                    and max_cost is not None
                ):
                    row[0] += min_cost
                    row[1] += max_cost
                    row[3] += 1

            summaries = [
                self.model(
                    stock_item_id=pk,
                    currency=currency,
                    min_cost=min_total if valid_count else None,
                    max_cost=max_total if valid_count else None,
                    incomplete=valid_count < entry_count,
                )
                for pk, (
                    min_total,
                    max_total,
                    entry_count,
                    valid_count,
                ) in totals.items()
            ]

            empty_ids = stock_item_ids - totals.keys()

            if empty_ids:
                self.filter(stock_item_id__in=empty_ids).delete()

            if summaries:
                upsert_kwargs = {
                    'update_conflicts': True,
                    'update_fields': [
                        'currency',
                        'min_cost',
                        'max_cost',
                        'incomplete',
                        'date',
                    ],
                }

                # Some database backends (e.g. MySQL) do not accept a conflict target
                if connections[self.db].features.supports_update_conflicts_with_target:
                    upsert_kwargs['unique_fields'] = ['stock_item']

                self.bulk_create(summaries, batch_size=500, **upsert_kwargs)

        # Schedule part pricing updates once the changes are committed - otherwise a
        # background worker could recalculate part pricing from uncommitted (or rolled back) data
        transaction.on_commit(
            lambda ids=frozenset(stock_item_ids): self.schedule_part_pricing_updates(
                ids
            ),
            using=self.db,
        )

    def schedule_part_pricing_updates(self, stock_item_ids):
        """Schedule a pricing update for the parts of the provided stock items.

        The purchase cost of a part is (optionally) calculated from the
        cost entries of its stock items (see PartPricing.update_purchase_cost).
        """
        if InvenTree.ready.isImportingData() or InvenTree.ready.isRunningMigrations():
            return

        if not InvenTree.ready.canAppAccessDatabase(
            allow_test=settings.TESTING_PRICING
        ):
            return

        from stock.models import StockItem

        part_ids = (
            StockItem.objects
            .filter(pk__in=stock_item_ids)
            .order_by()
            .values_list('part_id', flat=True)
            .distinct()
        )

        for part in Part.objects.filter(pk__in=list(part_ids)):
            part.schedule_pricing_update(create=True, refresh=False)


class StockItemCost(models.Model):
    """Cached summary of the total unit cost of a StockItem.

    This is the sum of all StockItemCostEntry records for the StockItem,
    in the default currency. It is recalculated automatically whenever
    an entry is created, updated or deleted, and should not be edited directly.

    Attributes:
        stock_item: The StockItem that this cost summary applies to (one-to-one)
        currency: Currency code for the min_cost and max_cost values
        min_cost: Sum of the (converted) minimum cost of all entries
        max_cost: Sum of the (converted) maximum cost of all entries
        incomplete: True if any of the entries could not be included (e.g. no exchange rate available)
        date: Date at which this summary was last calculated
    """

    class Meta:
        """Meta options for the StockItemCost model."""

        verbose_name = _('Stock Item Cost')

    objects = StockItemCostManager()

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the StockItemCost model."""
        return reverse('api-stock-cost-list')

    stock_item = models.OneToOneField(
        'stock.StockItem',
        on_delete=models.CASCADE,
        related_name='cost',
        verbose_name=_('Stock Item'),
        help_text=_('Stock item to which this cost summary applies'),
    )

    currency = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Currency'),
        help_text=_('Currency for the minimum and maximum cost'),
    )

    min_cost = models.DecimalField(
        max_digits=COST_MAX_DIGITS,
        decimal_places=COST_DECIMAL_PLACES,
        null=True,
        blank=True,
        verbose_name=_('Minimum Cost'),
        help_text=_('Minimum total unit cost, calculated from all cost entries'),
    )

    max_cost = models.DecimalField(
        max_digits=COST_MAX_DIGITS,
        decimal_places=COST_DECIMAL_PLACES,
        null=True,
        blank=True,
        verbose_name=_('Maximum Cost'),
        help_text=_('Maximum total unit cost, calculated from all cost entries'),
    )

    incomplete = models.BooleanField(
        default=False,
        verbose_name=_('Incomplete'),
        help_text=_('One or more cost entries could not be included in this summary'),
    )

    date = models.DateTimeField(
        auto_now=True,
        editable=False,
        verbose_name=_('Date'),
        help_text=_('Date at which this cost summary was last calculated'),
    )

    @property
    def min_cost_money(self):
        """Return the minimum cost as a Money instance (or None)."""
        return to_money(self.min_cost, self.currency)

    @property
    def max_cost_money(self):
        """Return the maximum cost as a Money instance (or None)."""
        return to_money(self.max_cost, self.currency)


def to_money(value, currency: str):
    """Return a Money instance for the provided value and currency, or None if either is missing."""
    if value is None or not currency:
        return None

    return Money(value, currency)
