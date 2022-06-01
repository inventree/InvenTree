"""Background tasks for the 'order' app"""

import logging

from django.utils.translation import gettext_lazy as _

from datetime import datetime, timedelta

import common.notifications
import InvenTree.helpers
from InvenTree.status_codes import PurchaseOrderStatus
import InvenTree.tasks
import order.models

from plugin.events import trigger_event


def notify_overdue_purchase_order(po: order.models.PurchaseOrder):
    """Notify users that a PurchaseOrder has just become 'overdue'"""

    print("Notifying overdue PO:", po)

    targets = []

    if po.created_by:
        targets.append(po.created_by)

    if po.responsible:
        # TODO: po.responsible is an Owner, and needs to be converted to a User!
        targets.append(po.responsible)

    name = _('Overdue Purchase Order')

    context = {
        'order': po,
        'name': name,
        'message': _(f'Purchase order {str(po)} is now overdue'),
        'link': InvenTree.helpers.construct_absolute_url(
            po.get_absolute_url(),
        ),
        'template': {
            'html': 'email/overdue_purchase_order.html',
            'subject': '[InvenTree] ' + name,
        }
    }

    event_name = 'order.overdue_purchase_order'

    # Send a notification to the appropriate users
    common.notifications.trigger_notification(
        po,
        event_name,
        targets=targets,
        context=context,
    )

    # Register a matching event to the plugin system
    trigger_event(
        event_name,
        purchase_order=po.pk,
    )


def check_overdue_purchase_orders():
    """Check if any outstanding PurchaseOrders have just become overdue:

    - This check is performed daily
    - Look at the 'target_date' of any outstanding PurchaseOrder objects
    - If the 'target_date' expired *yesterday* then the order is just out of date
    """

    yesterday = datetime.now().date() - timedelta(days=1)

    overdue_orders = order.models.PurchaseOrder.objects.filter(
        target_date=yesterday,
        status__in=PurchaseOrderStatus.OPEN
    )

    for po in overdue_orders:
        notify_overdue_purchase_order(po)
