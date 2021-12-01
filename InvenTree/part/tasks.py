# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.utils.translation import ugettext_lazy as _


import InvenTree.helpers
import InvenTree.tasks
import common.notifications

import part.models

logger = logging.getLogger("inventree")


def notify_low_stock(part: part.models.Part):
    context = {
        # Pass the "Part" object through to the template context
        'part': part,
        'link': InvenTree.helpers.construct_absolute_url(part.get_absolute_url()),
        'templates':{
            'html': 'email/low_stock_notification.html',
            'subject': "[InvenTree] " + _("Low stock notification"),
        },
    }

    common.notifications.trigger_notifaction(
        part,
        'part.notify_low_stock',
        receiver_fnc=part.get_subscribers,
        notification_context=context,
    )


def notify_low_stock_if_required(part: part.models.Part):
    """
    Check if the stock quantity has fallen below the minimum threshold of part.

    If true, notify the users who have subscribed to the part
    """

    # Run "up" the tree, to allow notification for "parent" parts
    parts = part.get_ancestors(include_self=True, ascending=True)

    for p in parts:
        if p.is_part_low_on_stock():
            InvenTree.tasks.offload_task(
                'part.tasks.notify_low_stock',
                p
            )
