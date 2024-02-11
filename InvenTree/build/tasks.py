"""Background task definitions for the BuildOrder app"""

from datetime import datetime, timedelta
from decimal import Decimal
import logging

from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string

from allauth.account.models import EmailAddress

from plugin.events import trigger_event
import common.notifications
import build.models
import InvenTree.email
import InvenTree.helpers_model
import InvenTree.tasks
from InvenTree.status_codes import BuildStatusGroups
from InvenTree.ready import isImportingData

import part.models as part_models


logger = logging.getLogger('inventree')


def update_build_order_lines(bom_item_pk: int):
    """Update all BuildOrderLineItem objects which reference a particular BomItem.

    This task is triggered when a BomItem is created or updated.
    """
    logger.info("Updating build order lines for BomItem %s", bom_item_pk)

    bom_item = part_models.BomItem.objects.filter(pk=bom_item_pk).first()

    # If the BomItem has been deleted, there is nothing to do
    if not bom_item:
        return

    assemblies = bom_item.get_assemblies()

    # Find all active builds which reference any of the parts
    builds = build.models.Build.objects.filter(
        part__in=list(assemblies),
        status__in=BuildStatusGroups.ACTIVE_CODES
    )

    # Iterate through each build, and update the relevant line items
    for bo in builds:
        # Try to find a matching build order line
        line = build.models.BuildLine.objects.filter(
            build=bo,
            bom_item=bom_item,
        ).first()

        q = bom_item.get_required_quantity(bo.quantity)

        if line:
            # Ensure quantity is correct
            if line.quantity != q:
                line.quantity = q
                line.save()
        else:
            # Create a new line item
            build.models.BuildLine.objects.create(
                build=bo,
                bom_item=bom_item,
                quantity=q,
            )

    if builds.count() > 0:
        logger.info("Updated %s build orders for part %s", builds.count(), bom_item.part)


def check_build_stock(build: build.models.Build):
    """Check the required stock for a newly created build order.

    Send an email out to any subscribed users if stock is low.
    """
    # Do not notify if we are importing data
    if isImportingData():
        return

    # Iterate through each of the parts required for this build

    lines = []

    if not build:
        logger.error("Invalid build passed to 'build.tasks.check_build_stock'")
        return

    try:
        part = build.part
    except part_models.Part.DoesNotExist:
        # Note: This error may be thrown during unit testing...
        logger.exception("Invalid build.part passed to 'build.tasks.check_build_stock'")
        return

    for bom_item in part.get_bom_items():

        sub_part = bom_item.sub_part

        # The 'in stock' quantity depends on whether the bom_item allows variants
        in_stock = sub_part.get_stock_count(include_variants=bom_item.allow_variants)

        allocated = sub_part.allocation_count()

        available = max(0, in_stock - allocated)

        required = Decimal(bom_item.quantity) * Decimal(build.quantity)

        if available < required:
            # There is not sufficient stock for this part

            lines.append({
                'link': InvenTree.helpers_model.construct_absolute_url(sub_part.get_absolute_url()),
                'part': sub_part,
                'in_stock': in_stock,
                'allocated': allocated,
                'available': available,
                'required': required,
            })

    if len(lines) == 0:
        # Nothing to do
        return

    # Are there any users subscribed to these parts?
    subscribers = build.part.get_subscribers()

    emails = EmailAddress.objects.filter(
        user__in=subscribers,
    )

    if len(emails) > 0:

        logger.info("Notifying users of stock required for build %s", build.pk)

        context = {
            'link': InvenTree.helpers_model.construct_absolute_url(build.get_absolute_url()),
            'build': build,
            'part': build.part,
            'lines': lines,
        }

        # Render the HTML message
        html_message = render_to_string('email/build_order_required_stock.html', context)

        subject = _("Stock required for build order")

        recipients = emails.values_list('email', flat=True)

        InvenTree.email.send_email(subject, '', recipients, html_message=html_message)


def notify_overdue_build_order(bo: build.models.Build):
    """Notify appropriate users that a Build has just become 'overdue'"""
    targets = []

    if bo.issued_by:
        targets.append(bo.issued_by)

    if bo.responsible:
        targets.append(bo.responsible)

    name = _('Overdue Build Order')

    context = {
        'order': bo,
        'name': name,
        'message': _(f"Build order {bo} is now overdue"),
        'link': InvenTree.helpers_model.construct_absolute_url(
            bo.get_absolute_url(),
        ),
        'template': {
            'html': 'email/overdue_build_order.html',
            'subject': name,
        }
    }

    event_name = 'build.overdue_build_order'

    # Send a notification to the appropriate users
    common.notifications.trigger_notification(
        bo,
        event_name,
        targets=targets,
        context=context
    )

    # Register a matching event to the plugin system
    trigger_event(event_name, build_order=bo.pk)


@InvenTree.tasks.scheduled_task(InvenTree.tasks.ScheduledTask.DAILY)
def check_overdue_build_orders():
    """Check if any outstanding BuildOrders have just become overdue

    - This check is performed daily
    - Look at the 'target_date' of any outstanding BuildOrder objects
    - If the 'target_date' expired *yesterday* then the order is just out of date
    """
    yesterday = datetime.now().date() - timedelta(days=1)

    overdue_orders = build.models.Build.objects.filter(
        target_date=yesterday,
        status__in=BuildStatusGroups.ACTIVE_CODES
    )

    for bo in overdue_orders:
        notify_overdue_build_order(bo)
