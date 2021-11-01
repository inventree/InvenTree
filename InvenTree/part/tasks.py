# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

from allauth.account.models import EmailAddress

from common.models import InvenTree

import InvenTree.helpers
import InvenTree.tasks

from part.models import Part

logger = logging.getLogger("inventree")


def notify_low_stock(part: Part):
    """
    Notify users who have starred a part when its stock quantity falls below the minimum threshold
    """

    logger.info(f"Sending low stock notification email for {part.full_name}")

    starred_users_email = EmailAddress.objects.filter(user__starred_parts__part=part)

    # TODO: In the future, include the part image in the email template

    if len(starred_users_email) > 0:
        logger.info(f"Notify users regarding low stock of {part.name}")
        context = {
            # Pass the "Part" object through to the template context
            'part': part,
            'link': InvenTree.helpers.construct_absolute_url(part.get_absolute_url()),
        }

        subject = _(f'[InvenTree] {part.name} is low on stock')
        html_message = render_to_string('email/low_stock_notification.html', context)
        recipients = starred_users_email.values_list('email', flat=True)

        InvenTree.tasks.send_email(subject, '', recipients, html_message=html_message)


def notify_low_stock_if_required(part: Part):
    """
    Check if the stock quantity has fallen below the minimum threshold of part.
    
    If true, notify the users who have subscribed to the part
    """

    if part.is_part_low_on_stock():
        InvenTree.tasks.offload_task(
            'part.tasks.notify_low_stock',
            part
        )
