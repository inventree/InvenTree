"""Background task definitions for the 'part' app."""

from datetime import datetime, timedelta
from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Model
from django.utils.translation import gettext_lazy as _

import structlog
from opentelemetry import trace

import common.currency
import common.notifications
import InvenTree.helpers_model
from common.settings import get_global_setting
from InvenTree.tasks import (
    ScheduledTask,
    check_daily_holdoff,
    offload_task,
    record_task_success,
    scheduled_task,
)

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger('inventree')


@tracer.start_as_current_span('notify_low_stock')
def notify_low_stock(part: Model):
    """Notify interested users that a part is 'low stock'.

    Rules:
    - Triggered when the available stock for a given part falls be low the configured threshold
    - A notification is delivered to any users who are 'subscribed' to this part
    """
    # Do not trigger low-stock notifications for inactive parts
    if not part.active:
        return

    name = _('Low stock notification')
    message = _(
        f'The available stock for {part.name} has fallen below the configured minimum level'
    )
    context = {
        'part': part,
        'name': name,
        'message': message,
        'link': InvenTree.helpers_model.construct_absolute_url(part.get_absolute_url()),
        'template': {'html': 'email/low_stock_notification.html', 'subject': name},
    }

    common.notifications.trigger_notification(
        part, 'part.notify_low_stock', target_fnc=part.get_subscribers, context=context
    )


@tracer.start_as_current_span('notify_stale_stock')
def notify_stale_stock(user, stale_items):
    """Notify a user about all their stale stock items in one consolidated email.

    Rules:
    - Triggered when stock items' expiry dates are within the configured STOCK_STALE_DAYS
    - One notification is delivered per user containing all their stale stock items

    Arguments:
        user: The user to notify
        stale_items: List of stale stock items for this user
    """
    if not stale_items:
        return

    name = _('Stale stock notification')
    item_count = len(stale_items)

    if item_count == 1:
        message = _('You have 1 stock item approaching its expiry date')
    else:
        message = _(f'You have {item_count} stock items approaching their expiry dates')

    # Add absolute URLs and days until expiry for each stock item
    stale_items_enhanced = []
    today = InvenTree.helpers.current_date()

    for stock_item in stale_items:
        # Calculate days until expiry to print it clearly in table in email later
        days_until_expiry = None
        expiry_status = _('No expiry date')

        if stock_item.expiry_date:
            days_diff = (stock_item.expiry_date - today).days

            if days_diff < 0:
                days_until_expiry = days_diff  # Keep negative value for template logic
                expiry_status = _(f'Expired {abs(days_diff)} days ago')
            elif days_diff == 0:
                days_until_expiry = 0
                expiry_status = _('Expires today')
            else:
                days_until_expiry = days_diff
                expiry_status = _(f'{days_until_expiry} days')

        item_data = {
            'stock_item': stock_item,
            'absolute_url': InvenTree.helpers_model.construct_absolute_url(
                stock_item.get_absolute_url()
            ),
            'days_until_expiry': days_until_expiry,
            'expiry_status': expiry_status,
        }
        stale_items_enhanced.append(item_data)

    context = {
        'stale_items': stale_items_enhanced,
        'item_count': item_count,
        'name': name,
        'message': message,
        'template': {'html': 'email/stale_stock_notification.html', 'subject': name},
    }

    # Use the first stock item as the trigger object for the notification system
    trigger_object = stale_items[0] if stale_items else None

    if trigger_object:
        common.notifications.trigger_notification(
            trigger_object,
            'stock.notify_stale_stock',
            targets=[user],
            context=context,
            check_recent=False,
        )


@tracer.start_as_current_span('notify_low_stock_if_required')
def notify_low_stock_if_required(part_id: int):
    """Check if the stock quantity has fallen below the minimum threshold of part.

    If true, notify the users who have subscribed to the part
    """
    from part.models import Part

    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        logger.warning(
            'notify_low_stock_if_required: Part with ID %s does not exist', part_id
        )
        return

    # Run "up" the tree, to allow notification for "parent" parts
    parts = part.get_ancestors(include_self=True, ascending=True)

    for p in parts:
        if part.active and p.is_part_low_on_stock():
            offload_task(notify_low_stock, p, group='notification')


@tracer.start_as_current_span('check_stale_stock')
@scheduled_task(ScheduledTask.DAILY)
def check_stale_stock():
    """Check all stock items for stale stock.

    This function runs daily and checks if any stock items are approaching their expiry date
    based on the STOCK_STALE_DAYS global setting.

    For any stale stock items found, notifications are sent to users who have subscribed
    to notifications for the respective parts. Each user receives one consolidated email
    containing all their stale stock items.
    """
    from stock.models import StockItem

    # Check if stock expiry functionality is enabled
    if not get_global_setting('STOCK_ENABLE_EXPIRY', False, cache=False):
        logger.info('Stock expiry functionality is not enabled - exiting')
        return

    # Check if STOCK_STALE_DAYS is configured
    stale_days = int(get_global_setting('STOCK_STALE_DAYS', 0, cache=False))

    if stale_days <= 0:
        logger.info('Stock stale days is not configured or set to 0 - exiting')
        return

    today = InvenTree.helpers.current_date()
    stale_threshold = today + timedelta(days=stale_days)

    # Find stock items that are stale (expiry date within STOCK_STALE_DAYS)
    stale_stock_items = StockItem.objects.filter(
        StockItem.IN_STOCK_FILTER,  # Only in-stock items
        expiry_date__isnull=False,  # Must have an expiry date
        expiry_date__lt=stale_threshold,  # Expiry date is within stale threshold
    ).select_related('part', 'location')  # Optimize queries

    if not stale_stock_items.exists():
        logger.info('No stale stock items found')
        return

    logger.info('Found %s stale stock items', stale_stock_items.count())

    # Group stale stock items by user subscriptions
    user_stale_items: dict[StockItem, list[StockItem]] = {}

    for stock_item in stale_stock_items:
        # Get all subscribers for this part
        subscribers = stock_item.part.get_subscribers()

        for user in subscribers:
            if user not in user_stale_items:
                user_stale_items[user] = []
            user_stale_items[user].append(stock_item)

    # Send one consolidated notification per user
    for user, items in user_stale_items.items():
        try:
            offload_task(notify_stale_stock, user, items, group='notification')
        except Exception as e:
            logger.error(
                'Error scheduling stale stock notification for user %s: %s',
                user.username,
                e,
            )

    logger.info(
        'Scheduled stale stock notifications for %s users', len(user_stale_items)
    )


@tracer.start_as_current_span('update_part_pricing')
def update_part_pricing(pricing: Model, counter: int = 0):
    """Update cached pricing data for the specified PartPricing instance.

    Arguments:
        pricing: The target PartPricing instance to be updated
        counter: How many times this function has been called in sequence
    """
    logger.info('Updating part pricing for %s', pricing.part)

    pricing.update_pricing(
        counter=counter,
        previous_min=pricing.overall_min,
        previous_max=pricing.overall_max,
    )


@tracer.start_as_current_span('check_missing_pricing')
@scheduled_task(ScheduledTask.DAILY)
def check_missing_pricing(limit=250):
    """Check for parts with missing or outdated pricing information.

    Tests for the following conditions:
    - Pricing information does not exist
    - Pricing information is "old"
    - Pricing information is in the wrong currency

    Arguments:
        limit: Maximum number of parts to process at once
    """
    from part.models import Part, PartPricing

    # Find any parts which have 'old' pricing information
    days = int(get_global_setting('PRICING_UPDATE_DAYS', 30))

    if days <= 0:
        # Task does not run if the interval is zero
        return

    # Find parts for which pricing information has never been updated
    results = PartPricing.objects.filter(updated=None)[:limit]

    if results.count() > 0:
        logger.info('Found %s parts with empty pricing', results.count())

        for pp in results:
            pp.schedule_for_update()

    stale_date = datetime.now().date() - timedelta(days=days)

    results = PartPricing.objects.filter(updated__lte=stale_date)[:limit]

    if results.count() > 0:
        logger.info('Found %s stale pricing entries', results.count())

        for pp in results:
            pp.schedule_for_update()

    # Find any pricing data which is in the wrong currency
    currency = common.currency.currency_code_default()
    results = PartPricing.objects.exclude(currency=currency)

    if results.count() > 0:
        logger.info('Found %s pricing entries in the wrong currency', results.count())

        for pp in results:
            pp.schedule_for_update()

    # Find any parts which do not have pricing information
    results = Part.objects.filter(pricing_data=None)[:limit]

    if results.count() > 0:
        logger.info('Found %s parts without pricing', results.count())

        for p in results:
            pricing = p.pricing
            pricing.save()
            pricing.schedule_for_update()


@tracer.start_as_current_span('scheduled_stocktake_reports')
@scheduled_task(ScheduledTask.DAILY)
def scheduled_stocktake_reports():
    """Scheduled tasks for creating automated 'stocktake' entries.

    A "stocktake" entry is a snapshot of the current stock levels for a given Part.

    This task runs daily, and performs the following functions:

    - Delete 'old' stocktake report files after the specified period
    - Generate new reports at the specified period
    """
    import part.stocktake
    from part.models import PartStocktake

    if get_global_setting('STOCKTAKE_DELETE_OLD_ENTRIES', False, cache=False):
        # First let's delete any old stock history entries
        delete_n_days = int(
            get_global_setting('STOCKTAKE_DELETE_DAYS', 365, cache=False)
        )

        threshold = datetime.now() - timedelta(days=delete_n_days)
        old_entries = PartStocktake.objects.filter(date__lt=threshold)

        if old_entries.count() > 0:
            logger.info('Deleting %s old stock entries', old_entries.count())
            old_entries.delete()

    # Next, check if stocktake functionality is enabled
    if not get_global_setting('STOCKTAKE_ENABLE', False, cache=False):
        logger.info('Stocktake functionality is not enabled - exiting')
        return

    report_n_days = int(get_global_setting('STOCKTAKE_AUTO_DAYS', 7, cache=False))

    if report_n_days < 1:
        logger.info('Stocktake auto reports are disabled, exiting')
        return

    if not check_daily_holdoff('STOCKTAKE_RECENT_REPORT', report_n_days):
        logger.info('Stock history was recently generated - exiting')
        return

    # Generate new stock history entries
    part.stocktake.perform_stocktake()

    # Record the date of this task run
    record_task_success('STOCKTAKE_RECENT_REPORT')


@tracer.start_as_current_span('rebuild_supplier_parts')
def rebuild_supplier_parts(part_id: int):
    """Rebuild all SupplierPart objects for a given part.

    This function is called when a bart part is changed,
    which may cause the native units of any supplier parts to be updated
    """
    from company.models import SupplierPart
    from part.models import Part

    try:
        prt = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return

    supplier_parts = SupplierPart.objects.filter(part=prt)

    n = supplier_parts.count()

    for supplier_part in supplier_parts:
        # Re-save the part, to ensure that the units have updated correctly
        try:
            supplier_part.full_clean()
            supplier_part.save()
        except ValidationError:
            pass

    if n > 0:
        logger.info("Rebuilt %s supplier parts for part '%s'", n, prt.name)


@tracer.start_as_current_span('check_bom_valid')
def check_bom_valid(part_id: int):
    """Recalculate the BOM checksum for all assemblies which include the specified Part.

    Arguments:
        part_id: The ID of the part for which to recalculate the BOM checksum.
    """
    from part.models import Part

    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        logger.warning('check_bom_valid: Part with ID %s does not exist', part_id)
        return

    valid = part.is_bom_valid()

    if valid != part.bom_validated:
        part.bom_validated = valid
        part.save()


@tracer.start_as_current_span('validate_bom')
def validate_bom(part_id: int, valid: bool, user_id: Optional[int] = None):
    """Run BOM validation for the specified Part.

    Arguments:
        part_id: The ID of the part for which to validate the BOM.
        valid: Boolean indicating whether the BOM is valid or not.
        user_id: Optional ID of the user performing the validation.
    """
    from django.contrib.auth import get_user_model

    from part.models import Part

    User = get_user_model()

    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        logger.warning('validate_bom: Part with ID %s does not exist', part_id)
        return

    if user_id:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            user = None
    else:
        user = None

    part.validate_bom(user, valid=valid)
