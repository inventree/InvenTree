"""Background tasks for the 'order' app"""

from django.utils.translation import gettext_lazy as _

from datetime import datetime, timedelta

import common.notifications
import InvenTree.helpers
from InvenTree.status_codes import PurchaseOrderStatus, SalesOrderStatus
import InvenTree.tasks
import order.models

from plugin.events import trigger_event


def notify_overdue_purchase_order(po: order.models.PurchaseOrder):
    """Notify users that a PurchaseOrder has just become 'overdue'"""

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
        'link': InvenTree.helpers.construct_absolute_url(
            po.get_absolute_url(),
        ),
        'template': {
            'html': 'email/overdue_purchase_order.html',
            'subject': f'[InvenTree] {name}',
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


def notify_overdue_sales_order(so: order.models.SalesOrder):
    """Notify appropriate users that a SalesOrder has just become 'overdue'"""

    targets = []

    if so.created_by:
        targets.append(so.created_by)
    
    if so.responsible:
        targets.append(so.responsible)

    name = _('Overdue Sales Order')

    context = {
        'order': so,
        'name': name,
        'message': _(f"Sales order {so} is now overdue"),
        'link': InvenTree.helpers.construct_absolute_url(
            so.get_absolute_url(),
        ),
        'template': {
            'html': 'email/overdue_sales_order.html',
            'subject': f'[InvenTree] {name}'
        }
    }

    event_name = 'order.overdue_sales_order'

    # Send a notification to the appropriate users
    common.notifications.trigger_notification(
        so,
        event_name,
        targets=targets,
        context=context,
    )

    # Register a matching event to the plugin system
    trigger_event(
        event_name,
        sales_order=so.pk,
    )


def check_overdue_sales_orders():
    """Check if any outstanding SalesOrders have just become overdueL
    
    - This check is performed daily
    - Look at the 'target_date' of any outstanding SalesOrder objects
    - If the 'target_date' expired *yesterday* then the order is just out of date
    """
    
    yesterday = datetime.now().date() - timedelta(days=1)

    overdue_orders = order.models.SalesOrder.objects.filter(
        target_date=yesterday,
        status__in=SalesOrderStatus.OPEN
    )

    for po in overdue_orders:
        notify_overdue_sales_order(po)
