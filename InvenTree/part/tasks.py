"""Background task definitions for the 'part' app"""

import logging

from django.utils.translation import gettext_lazy as _

import common.notifications
import InvenTree.helpers
import InvenTree.tasks
import part.models

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
            'subject': "[InvenTree] " + name,
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
