"""Background task definitions for the BuildOrder app"""

from decimal import Decimal
import logging

from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string

from allauth.account.models import EmailAddress

import build.models
import InvenTree.helpers
import InvenTree.tasks
from InvenTree.ready import isImportingData

import part.models as part_models


logger = logging.getLogger('inventree')


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
        logger.error("Invalid build.part passed to 'build.tasks.check_build_stock'")
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
