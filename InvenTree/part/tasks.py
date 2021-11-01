# Author: Roche Christopher
# Created at 10:26 AM on 31/10/21

import logging

from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

from InvenTree import tasks as inventree_tasks
from part.models import Part

logger = logging.getLogger("inventree")


def notify_low_stock(part: Part):
    """
    Notify users who have starred a part when its stock quantity falls below the minimum threshold
    """

    from allauth.account.models import EmailAddress
    starred_users_email = EmailAddress.objects.filter(user__starred_parts__part=part)

    if len(starred_users_email) > 0:
        logger.info(f"Notify users regarding low stock of {part.name}")
        context = {
            'part_name': part.name,
            # Part url can be used to open the page of part in application from the email.
            # It can be facilitated when the application base url is accessible programmatically.
            # 'part_url': f'{application_base_url}/part/{stock_item.part.id}',

            # quantity is in decimal field datatype. Since the same datatype is used in models,
            # it is not converted to number/integer,
            'part_quantity': part.total_stock,
            'minimum_quantity': part.minimum_stock
        }
        subject = _(f'Attention! {part.name} is low on stock')
        html_message = render_to_string('stock/low_stock_notification.html', context)
        recipients = starred_users_email.values_list('email', flat=True)
        inventree_tasks.send_email(subject, '', recipients, html_message=html_message)


def notify_low_stock_if_required(part: Part):
    """
    Check if the stock quantity has fallen below the minimum threshold of part. If yes, notify the users who have
    starred the part
    """

    if part.is_part_low_on_stock():
        inventree_tasks.offload_task(
            'part.tasks.notify_low_stock',
            part
        )
