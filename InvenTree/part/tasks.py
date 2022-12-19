"""Background task definitions for the 'part' app"""

import logging
from datetime import datetime, timedelta

from django.utils.translation import gettext_lazy as _

import common.models
import common.notifications
import common.settings
import InvenTree.helpers
import InvenTree.tasks
import part.models
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
