"""Database model definitions for the 'pricing' app."""

from datetime import timedelta

from django.conf import settings
from django.db import models
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

logger = structlog.get_logger('inventree')


class PartPricing(common.models.MetaMixin):
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

    class Meta:
        """Metaclass providing extra model definition."""

        # Table name retained from when this model was part of the 'part' app
        db_table = 'part_partpricing'

    # When calculating assembly pricing, we limit the depth of the calculation
    MAX_PRICING_DEPTH = 50

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
                bom_item_min *= bom_item.quantity
                cumulative_min += self.convert(bom_item_min)

                any_min_elements = True

            if bom_item_max is not None:
                bom_item_max *= bom_item.quantity
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

        # Also check if manual stock item pricing is included
        if get_global_setting('PRICING_USE_STOCK_PRICING', True):
            items = self.part.stock_items.all()

            # Limit to stock items updated within a certain window
            days = int(get_global_setting('PRICING_STOCK_ITEM_AGE_DAYS', 0))

            if days > 0:
                date_threshold = InvenTree.helpers.current_date() - timedelta(days=days)
                items = items.filter(updated__gte=date_threshold)

            for item in items:
                cost = self.convert(item.purchase_price)

                # Skip if the cost could not be converted (for some reason)
                if cost is None:
                    continue

                if purchase_min is None or cost < purchase_min:
                    purchase_min = cost

                if purchase_max is None or cost > purchase_max:
                    purchase_max = cost

        self.purchase_cost_min = purchase_min
        self.purchase_cost_max = purchase_max

        if save:
            self.save()

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


class PartSellPriceBreak(common.models.PriceBreak):
    """Represents a price break for selling this part."""

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


class PartInternalPriceBreak(common.models.PriceBreak):
    """Represents a price break for internally selling this part."""

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
