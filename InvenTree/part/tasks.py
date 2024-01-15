"""Background task definitions for the 'part' app."""

import logging
import random
import time
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import common.models
import common.notifications
import common.settings
import company.models
import InvenTree.helpers
import InvenTree.helpers_model
import InvenTree.tasks
import part.models
import part.stocktake
from InvenTree.tasks import (
    ScheduledTask,
    check_daily_holdoff,
    record_task_success,
    scheduled_task,
)

logger = logging.getLogger('inventree')


def notify_low_stock(part: part.models.Part):
    """Notify interested users that a part is 'low stock'.

    Rules:
    - Triggered when the available stock for a given part falls be low the configured threhsold
    - A notification is delivered to any users who are 'subscribed' to this part
    """
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


def notify_low_stock_if_required(part: part.models.Part):
    """Check if the stock quantity has fallen below the minimum threshold of part.

    If true, notify the users who have subscribed to the part
    """
    # Run "up" the tree, to allow notification for "parent" parts
    parts = part.get_ancestors(include_self=True, ascending=True)

    for p in parts:
        if p.is_part_low_on_stock():
            InvenTree.tasks.offload_task(notify_low_stock, p)


def update_part_pricing(pricing: part.models.PartPricing, counter: int = 0):
    """Update cached pricing data for the specified PartPricing instance.

    Arguments:
        pricing: The target PartPricing instance to be updated
        counter: How many times this function has been called in sequence
    """
    logger.info('Updating part pricing for %s', pricing.part)

    pricing.update_pricing(counter=counter)


@scheduled_task(InvenTree.tasks.ScheduledTask.DAILY)
def check_missing_pricing(limit=250):
    """Check for parts with missing or outdated pricing information.

    Tests for the following conditions:
    - Pricing information does not exist
    - Pricing information is "old"
    - Pricing information is in the wrong currency

    Arguments:
        limit: Maximum number of parts to process at once
    """
    # Find parts for which pricing information has never been updated
    results = part.models.PartPricing.objects.filter(updated=None)[:limit]

    if results.count() > 0:
        logger.info('Found %s parts with empty pricing', results.count())

        for pp in results:
            pp.schedule_for_update()

    # Find any parts which have 'old' pricing information
    days = int(common.models.InvenTreeSetting.get_setting('PRICING_UPDATE_DAYS', 30))
    stale_date = datetime.now().date() - timedelta(days=days)

    results = part.models.PartPricing.objects.filter(updated__lte=stale_date)[:limit]

    if results.count() > 0:
        logger.info('Found %s stale pricing entries', results.count())

        for pp in results:
            pp.schedule_for_update()

    # Find any pricing data which is in the wrong currency
    currency = common.settings.currency_code_default()
    results = part.models.PartPricing.objects.exclude(currency=currency)

    if results.count() > 0:
        logger.info('Found %s pricing entries in the wrong currency', results.count())

        for pp in results:
            pp.schedule_for_update()

    # Find any parts which do not have pricing information
    results = part.models.Part.objects.filter(pricing_data=None)[:limit]

    if results.count() > 0:
        logger.info('Found %s parts without pricing', results.count())

        for p in results:
            pricing = p.pricing
            pricing.save()
            pricing.schedule_for_update()


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
    delete_n_days = int(
        common.models.InvenTreeSetting.get_setting(
            'STOCKTAKE_DELETE_REPORT_DAYS', 30, cache=False
        )
    )
    threshold = datetime.now() - timedelta(days=delete_n_days)
    old_reports = part.models.PartStocktakeReport.objects.filter(date__lt=threshold)

    if old_reports.count() > 0:
        logger.info('Deleting %s stale stocktake reports', old_reports.count())
        old_reports.delete()

    # Next, check if stocktake functionality is enabled
    if not common.models.InvenTreeSetting.get_setting(
        'STOCKTAKE_ENABLE', False, cache=False
    ):
        logger.info('Stocktake functionality is not enabled - exiting')
        return

    report_n_days = int(
        common.models.InvenTreeSetting.get_setting(
            'STOCKTAKE_AUTO_DAYS', 0, cache=False
        )
    )

    if report_n_days < 1:
        logger.info('Stocktake auto reports are disabled, exiting')
        return

    if not check_daily_holdoff('STOCKTAKE_RECENT_REPORT', report_n_days):
        logger.info('Stocktake report was recently generated - exiting')
        return

    # Let's start a new stocktake report for all parts
    part.stocktake.generate_stocktake_report(update_parts=True)

    # Record the date of this report
    record_task_success('STOCKTAKE_RECENT_REPORT')


def rebuild_parameters(template_id):
    """Rebuild all parameters for a given template.

    This function is called when a base template is changed,
    which may cause the base unit to be adjusted.
    """
    try:
        template = part.models.PartParameterTemplate.objects.get(pk=template_id)
    except part.models.PartParameterTemplate.DoesNotExist:
        return

    parameters = part.models.PartParameter.objects.filter(template=template)

    n = 0

    for parameter in parameters:
        # Update the parameter if the numeric value has changed
        value_old = parameter.data_numeric
        parameter.calculate_numeric_value()

        if value_old != parameter.data_numeric:
            parameter.full_clean()
            parameter.save()
            n += 1

    if n > 0:
        logger.info("Rebuilt %s parameters for template '%s'", n, template.name)


def rebuild_supplier_parts(part_id):
    """Rebuild all SupplierPart objects for a given part.

    This function is called when a bart part is changed,
    which may cause the native units of any supplier parts to be updated
    """
    try:
        prt = part.models.Part.objects.get(pk=part_id)
    except part.models.Part.DoesNotExist:
        return

    supplier_parts = company.models.SupplierPart.objects.filter(part=prt)

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
