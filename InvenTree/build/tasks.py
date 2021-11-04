# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

from allauth.account.models import EmailAddress

from common.models import NotificationEntry

import build.models
import InvenTree.helpers
import InvenTree.tasks


logger = logging.getLogger('inventree')


def check_build_stock(build: build.models.Build):
    """
    Check the required stock for a newly created build order,
    and send an email out to any subscribed users if stock is low.
    """

    # Iterate through each of the parts required for this build

    lines = []

    for bom_item in build.part.get_bom_items():

        sub_part = bom_item.sub_part

        # The 'in stock' quantity depends on whether the bom_item allows variants
        in_stock = sub_part.get_stock_count(include_variants=bom_item.allow_variants)

        allocated = sub_part.allocation_count()

        available = max(0, in_stock - allocated)

        required = bom_item.quantity * build.quantity

        if available < required:
            # There is not sufficient stock for this part

            lines.append({
                'link': InvenTree.helpers.construct_absolute_url(sub_part.get_absolute_url()),
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

        logger.info(f"Notifying users of stock required for build {build.pk}")

        context = {
            'link': InvenTree.helpers.construct_absolute_url(build.get_absolute_url()),
            'build': build,
            'part': build.part,
            'lines': lines,
        }

        # Render the HTML message
        html_message = render_to_string('email/build_order_required_stock.html', context)

        subject = "[InvenTree] " + _("Stock required for build order")

        recipients = emails.values_list('email', flat=True)

        InvenTree.tasks.send_email(subject, '', recipients, html_message=html_message)
