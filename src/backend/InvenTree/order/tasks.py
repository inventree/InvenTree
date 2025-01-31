"""Background tasks for the 'order' app."""

from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import transaction
from django.utils.translation import gettext_lazy as _

import structlog

import common.notifications
import InvenTree.helpers_model
import order.models
from InvenTree.tasks import ScheduledTask, scheduled_task
from order.events import PurchaseOrderEvents, SalesOrderEvents
from order.status_codes import PurchaseOrderStatusGroups, SalesOrderStatusGroups
from plugin.events import trigger_event

logger = structlog.get_logger('inventree')


def notify_overdue_purchase_order(po: order.models.PurchaseOrder):
    """Notify users that a PurchaseOrder has just become 'overdue'."""
    targets = []

    if po.created_by:
        targets.append(po.created_by)

    if po.responsible:
        targets.append(po.responsible)

    name = _('Overdue Purchase Order')

    context = {
        'order': po,
        'name': name,
        'message': _(f'Purchase order {po} is now overdue'),
        'link': InvenTree.helpers_model.construct_absolute_url(po.get_absolute_url()),
        'template': {'html': 'email/overdue_purchase_order.html', 'subject': name},
    }

    event_name = PurchaseOrderEvents.OVERDUE

    # Send a notification to the appropriate users
    common.notifications.trigger_notification(
        po, event_name, targets=targets, context=context
    )

    # Register a matching event to the plugin system
    trigger_event(event_name, purchase_order=po.pk)


@scheduled_task(ScheduledTask.DAILY)
def check_overdue_purchase_orders():
    """Check if any outstanding PurchaseOrders have just become overdue.

    Rules:
    - This check is performed daily
    - Look at the 'target_date' of any outstanding PurchaseOrder objects
    - If the 'target_date' expired *yesterday* then the order is just out of date
    """
    yesterday = datetime.now().date() - timedelta(days=1)

    overdue_orders = order.models.PurchaseOrder.objects.filter(
        target_date=yesterday, status__in=PurchaseOrderStatusGroups.OPEN
    )

    for po in overdue_orders:
        notify_overdue_purchase_order(po)


def notify_overdue_sales_order(so: order.models.SalesOrder):
    """Notify appropriate users that a SalesOrder has just become 'overdue'."""
    targets = []

    if so.created_by:
        targets.append(so.created_by)

    if so.responsible:
        targets.append(so.responsible)

    name = _('Overdue Sales Order')

    context = {
        'order': so,
        'name': name,
        'message': _(f'Sales order {so} is now overdue'),
        'link': InvenTree.helpers_model.construct_absolute_url(so.get_absolute_url()),
        'template': {'html': 'email/overdue_sales_order.html', 'subject': name},
    }

    event_name = SalesOrderEvents.OVERDUE

    # Send a notification to the appropriate users
    common.notifications.trigger_notification(
        so, event_name, targets=targets, context=context
    )

    # Register a matching event to the plugin system
    trigger_event(event_name, sales_order=so.pk)


@scheduled_task(ScheduledTask.DAILY)
def check_overdue_sales_orders():
    """Check if any outstanding SalesOrders have just become overdue.

    - This check is performed daily
    - Look at the 'target_date' of any outstanding SalesOrder objects
    - If the 'target_date' expired *yesterday* then the order is just out of date
    """
    yesterday = datetime.now().date() - timedelta(days=1)

    overdue_orders = order.models.SalesOrder.objects.filter(
        target_date=yesterday, status__in=SalesOrderStatusGroups.OPEN
    )

    for po in overdue_orders:
        notify_overdue_sales_order(po)


def complete_sales_order_shipment(shipment_id: int, user_id: int) -> None:
    """Complete allocations for a pending shipment against a SalesOrder.

    At this stage, the shipment is assumed to be complete,
    and we need to perform the required "processing" tasks.
    """
    try:
        shipment = order.models.SalesOrderShipment.objects.get(pk=shipment_id)
    except Exception:
        # Shipping object does not exist
        logger.warning(
            'Failed to complete shipment - no matching SalesOrderShipment for ID <%s>',
            shipment_id,
        )
        return

    try:
        user = User.objects.get(pk=user_id)
    except Exception:
        user = None

    logger.info('Completing SalesOrderShipment <%s>', shipment)

    with transaction.atomic():
        for allocation in shipment.allocations.all():
            allocation.complete_allocation(user=user)
