"""Background task definitions for the 'part' app"""

import io
import logging
import random
import time
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _

import tablib
from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money

import common.models
import common.notifications
import common.settings
import InvenTree.helpers
import InvenTree.tasks
import part.models
import stock.models
from InvenTree.tasks import ScheduledTask, scheduled_task

logger = logging.getLogger("inventree")


def notify_low_stock(part: part.models.Part):
    """Notify interested users that a part is 'low stock':

    - Triggered when the available stock for a given part falls be low the configured threhsold
    - A notification is delivered to any users who are 'subscribed' to this part
    """
    name = _("Low stock notification")
    message = _(f'The available stock for {part.name} has fallen below the configured minimum level')
    context = {
        'part': part,
        'name': name,
        'message': message,
        'link': InvenTree.helpers.construct_absolute_url(part.get_absolute_url()),
        'template': {
            'html': 'email/low_stock_notification.html',
            'subject': name,
        },
    }

    common.notifications.trigger_notification(
        part,
        'part.notify_low_stock',
        target_fnc=part.get_subscribers,
        context=context,
    )


def notify_low_stock_if_required(part: part.models.Part):
    """Check if the stock quantity has fallen below the minimum threshold of part.

    If true, notify the users who have subscribed to the part
    """
    # Run "up" the tree, to allow notification for "parent" parts
    parts = part.get_ancestors(include_self=True, ascending=True)

    for p in parts:
        if p.is_part_low_on_stock():
            InvenTree.tasks.offload_task(
                notify_low_stock,
                p
            )


def update_part_pricing(pricing: part.models.PartPricing, counter: int = 0):
    """Update cached pricing data for the specified PartPricing instance

    Arguments:
        pricing: The target PartPricing instance to be updated
        counter: How many times this function has been called in sequence
    """

    logger.info(f"Updating part pricing for {pricing.part}")

    pricing.update_pricing(counter=counter)


@scheduled_task(ScheduledTask.DAILY)
def check_missing_pricing(limit=250):
    """Check for parts with missing or outdated pricing information:

    - Pricing information does not exist
    - Pricing information is "old"
    - Pricing information is in the wrong currency

    Arguments:
        limit: Maximum number of parts to process at once
    """

    # Find parts for which pricing information has never been updated
    results = part.models.PartPricing.objects.filter(updated=None)[:limit]

    if results.count() > 0:
        logger.info(f"Found {results.count()} parts with empty pricing")

        for pp in results:
            pp.schedule_for_update()

    # Find any parts which have 'old' pricing information
    days = int(common.models.InvenTreeSetting.get_setting('PRICING_UPDATE_DAYS', 30))
    stale_date = datetime.now().date() - timedelta(days=days)

    results = part.models.PartPricing.objects.filter(updated__lte=stale_date)[:limit]

    if results.count() > 0:
        logger.info(f"Found {results.count()} stale pricing entries")

        for pp in results:
            pp.schedule_for_update()

    # Find any pricing data which is in the wrong currency
    currency = common.settings.currency_code_default()
    results = part.models.PartPricing.objects.exclude(currency=currency)

    if results.count() > 0:
        logger.info(f"Found {results.count()} pricing entries in the wrong currency")

        for pp in results:
            pp.schedule_for_update()

    # Find any parts which do not have pricing information
    results = part.models.Part.objects.filter(pricing_data=None)[:limit]

    if results.count() > 0:
        logger.info(f"Found {results.count()} parts without pricing")

        for p in results:
            pricing = p.pricing
            pricing.save()
            pricing.schedule_for_update()


def perform_stocktake(target: part.models.Part, user: User, note: str = '', commit=True, **kwargs):
    """Perform stocktake action on a single part.

    arguments:
        target: A single Part model instance
        commit: If True (default) save the result to the database
        user: User who requested this stocktake

    Returns:
        PartStocktake: A new PartStocktake model instance (for the specified Part)
    """

    # Grab all "available" stock items for the Part
    stock_entries = target.stock_entries(in_stock=True, include_variants=True)

    # Cache min/max pricing information for this Part
    pricing = target.pricing

    if not pricing.is_valid:
        # If pricing is not valid, let's update
        logger.info(f"Pricing not valid for {target} - updating")
        pricing.update_pricing(cascade=False)
        pricing.refresh_from_db()

    base_currency = common.settings.currency_code_default()

    total_quantity = 0
    total_cost_min = Money(0, base_currency)
    total_cost_max = Money(0, base_currency)

    for entry in stock_entries:

        # Update total quantity value
        total_quantity += entry.quantity

        has_pricing = False

        # Update price range values
        if entry.purchase_price:
            # If purchase price is available, use that
            try:
                pp = convert_money(entry.purchase_price, base_currency) * entry.quantity
                total_cost_min += pp
                total_cost_max += pp
                has_pricing = True
            except MissingRate:
                logger.warning(f"MissingRate exception occured converting {entry.purchase_price} to {base_currency}")

        if not has_pricing:
            # Fall back to the part pricing data
            p_min = pricing.overall_min or pricing.overall_max
            p_max = pricing.overall_max or pricing.overall_min

            if p_min or p_max:
                try:
                    total_cost_min += convert_money(p_min, base_currency) * entry.quantity
                    total_cost_max += convert_money(p_max, base_currency) * entry.quantity
                except MissingRate:
                    logger.warning(f"MissingRate exception occurred converting {p_min}:{p_max} to {base_currency}")

    # Construct PartStocktake instance
    instance = part.models.PartStocktake(
        part=target,
        item_count=stock_entries.count(),
        quantity=total_quantity,
        cost_min=total_cost_min,
        cost_max=total_cost_max,
        note=note,
        user=user,
    )

    if commit:
        instance.save()

    return instance


def generate_stocktake_report(**kwargs):
    """Generated a new stocktake report.

    Note that this method should be called only by the background worker process!

    Unless otherwise specified, the stocktake report is generated for *all* Part instances.
    Optional filters can by supplied via the kwargs

    kwargs:
        user: The user who requested this stocktake (set to None for automated stocktake)
        part: Optional Part instance to filter by (including variant parts)
        category: Optional PartCategory to filter results
        location: Optional StockLocation to filter results
        generate_report: If True, generate a stocktake report from the calculated data (default=True)
        update_parts: If True, save stocktake information against each filtered Part (default = True)
    """

    parts = part.models.Part.objects.all()
    user = kwargs.get('user', None)

    generate_report = kwargs.get('generate_report', True)
    update_parts = kwargs.get('update_parts', True)

    # Filter by 'Part' instance
    if p := kwargs.get('part', None):
        variants = p.get_descendants(include_self=True)
        parts = parts.filter(
            pk__in=[v.pk for v in variants]
        )

    # Filter by 'Category' instance (cascading)
    if category := kwargs.get('category', None):
        categories = category.get_descendants(include_self=True)
        parts = parts.filter(category__in=categories)

    # Filter by 'Location' instance (cascading)
    # Stocktake report will be limited to parts which have stock items within this location
    if location := kwargs.get('location', None):
        # Extract flat list of all sublocations
        locations = list(location.get_descendants(include_self=True))

        # Items which exist within these locations
        items = stock.models.StockItem.objects.filter(location__in=locations)

        # List of parts which exist within these locations
        unique_parts = items.order_by().values('part').distinct()

        parts = parts.filter(
            pk__in=[result['part'] for result in unique_parts]
        )

    # Exit if filters removed all parts
    n_parts = parts.count()

    if n_parts == 0:
        logger.info("No parts selected for stocktake report - exiting")
        return

    logger.info(f"Generating new stocktake report for {n_parts} parts")

    base_currency = common.settings.currency_code_default()

    # Construct an initial dataset for the stocktake report
    dataset = tablib.Dataset(
        headers=[
            _('Part ID'),
            _('Part Name'),
            _('Part Description'),
            _('Category ID'),
            _('Category Name'),
            _('Stock Items'),
            _('Total Quantity'),
            _('Total Cost Min') + f' ({base_currency})',
            _('Total Cost Max') + f' ({base_currency})',
        ]
    )

    parts = parts.prefetch_related('category', 'stock_items')

    # Simple profiling for this task
    t_start = time.time()

    # Keep track of each individual "stocktake" we perform.
    # They may be bulk-commited to the database afterwards
    stocktake_instances = []

    total_parts = 0

    # Iterate through each Part which matches the filters above
    for p in parts:

        # Create a new stocktake for this part (do not commit, this will take place later on)
        stocktake = perform_stocktake(p, user, commit=False)

        if stocktake.quantity == 0:
            # Skip rows with zero total quantity
            continue

        total_parts += 1

        stocktake_instances.append(stocktake)

        # Add a row to the dataset
        dataset.append([
            p.pk,
            p.full_name,
            p.description,
            p.category.pk if p.category else '',
            p.category.name if p.category else '',
            stocktake.item_count,
            stocktake.quantity,
            InvenTree.helpers.normalize(stocktake.cost_min.amount),
            InvenTree.helpers.normalize(stocktake.cost_max.amount),
        ])

    # Save a new PartStocktakeReport instance
    buffer = io.StringIO()
    buffer.write(dataset.export('csv'))

    today = datetime.now().date().isoformat()
    filename = f"InvenTree_Stocktake_{today}.csv"
    report_file = ContentFile(buffer.getvalue(), name=filename)

    if generate_report:
        report_instance = part.models.PartStocktakeReport.objects.create(
            report=report_file,
            part_count=total_parts,
            user=user
        )

        # Notify the requesting user
        if user:

            common.notifications.trigger_notification(
                report_instance,
                category='generate_stocktake_report',
                context={
                    'name': _('Stocktake Report Available'),
                    'message': _('A new stocktake report is available for download'),
                },
                targets=[
                    user,
                ]
            )

    # If 'update_parts' is set, we save stocktake entries for each individual part
    if update_parts:
        # Use bulk_create for efficient insertion of stocktake
        part.models.PartStocktake.objects.bulk_create(
            stocktake_instances,
            batch_size=500,
        )

    t_stocktake = time.time() - t_start
    logger.info(f"Generated stocktake report for {total_parts} parts in {round(t_stocktake, 2)}s")


@scheduled_task(ScheduledTask.DAILY)
def scheduled_stocktake_reports():
    """Scheduled tasks for creating automated stocktake reports.

    This task runs daily, and performs the following functions:

    - Delete 'old' stocktake report files after the specified period
    - Generate new reports at the specified period
    """

    # Sleep a random number of seconds to prevent worker conflict
    time.sleep(random.randint(1, 5))

    # First let's delete any old stocktake reports
    delete_n_days = int(common.models.InvenTreeSetting.get_setting('STOCKTAKE_DELETE_REPORT_DAYS', 30, cache=False))
    threshold = datetime.now() - timedelta(days=delete_n_days)
    old_reports = part.models.PartStocktakeReport.objects.filter(date__lt=threshold)

    if old_reports.count() > 0:
        logger.info(f"Deleting {old_reports.count()} stale stocktake reports")
        old_reports.delete()

    # Next, check if stocktake functionality is enabled
    if not common.models.InvenTreeSetting.get_setting('STOCKTAKE_ENABLE', False, cache=False):
        logger.info("Stocktake functionality is not enabled - exiting")
        return

    report_n_days = int(common.models.InvenTreeSetting.get_setting('STOCKTAKE_AUTO_DAYS', 0, cache=False))

    if report_n_days < 1:
        logger.info("Stocktake auto reports are disabled, exiting")
        return

    # How long ago was last full stocktake report generated?
    last_report = common.models.InvenTreeSetting.get_setting('STOCKTAKE_RECENT_REPORT', '', cache=False)

    try:
        last_report = datetime.fromisoformat(last_report)
    except ValueError:
        last_report = None

    if last_report:
        # Do not attempt if the last report was within the minimum reporting period
        threshold = datetime.now() - timedelta(days=report_n_days)

        if last_report > threshold:
            logger.info("Automatic stocktake report was recently generated - exiting")
            return

    # Let's start a new stocktake report for all parts
    generate_stocktake_report(update_parts=True)

    # Record the date of this report
    common.models.InvenTreeSetting.set_setting('STOCKTAKE_RECENT_REPORT', datetime.now().isoformat(), None)
