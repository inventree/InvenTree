import logging
from datetime import timedelta

from django.conf import settings
from django.template.loader import render_to_string

from allauth.account.models import EmailAddress

from InvenTree.helpers import inheritors
from common.models import NotificationEntry, NotificationMessage
import InvenTree.tasks


logger = logging.getLogger('inventree')


# region notification classes
# region base classes
class NotificationMethod:
    METHOD_NAME = ''

    def __init__(self, obj, entry_name, receivers) -> None:
        # Check if a sending fnc is defined
        if (not hasattr(self, 'send')) and (not hasattr(self, 'send_bulk')):
            raise NotImplementedError('A NotificationMethod must either define a `send` or a `send_bulk` method')

        # No method name is no good
        if self.METHOD_NAME in ('', None):
            raise NotImplementedError(f'The NotificationMethod {self.__class__} did not provide a METHOD_NAME')

        # Define arguments
        self.obj = obj
        self.entry_name = entry_name
        self.receivers = receivers

        # Gather recipients
        self.recipients = self.get_recipients()

    def get_recipients(self):
        raise NotImplementedError('The `get_recipients` method must be implemented!')

    def setup(self):
        return True

    def cleanup(self):
        return True


class SingleNotificationMethod(NotificationMethod):
    def send(self, receiver, context):
        raise NotImplementedError('The `send` method must be overriden!')


class BulkNotificationMethod(NotificationMethod):
    def send_bulk(self, context):
        raise NotImplementedError('The `send` method must be overriden!')
# endregion


# region implementations
class EmailNotification(BulkNotificationMethod):
    METHOD_NAME = 'mail'

    def get_recipients(self):
        return EmailAddress.objects.filter(
            user__in=self.receivers,
        )

    def send_bulk(self, context):
        # TODO: In the future, include the part image in the email template

        if 'template' not in context:
            raise NotImplementedError('Templates must be provided in the `context`')
        if 'html' not in context['template']:
            raise NotImplementedError("template['html'] must be provided in the `context`")
        if 'subject' not in context['template']:
            raise NotImplementedError("template['subject'] must be provided in the `context`")

        html_message = render_to_string(context['template']['html'], context)
        recipients = self.recipients.values_list('email', flat=True)

        InvenTree.tasks.send_email(context['template']['subject'], '', recipients, html_message=html_message)

        return True

class UIMessageNotification(SingleNotificationMethod):
    METHOD_NAME = 'ui_message'

    def get_recipients(self):
        return self.receivers

    def send(self, receiver, context):
        NotificationMessage.objects.create(
            target_object = self.obj,
            source_object = receiver,
            user = receiver,
            category = self.entry_name,
            name = context['name'],
            message = context['message'],
        )
# endregion
# endregion


def trigger_notifaction(obj, entry_name=None, obj_ref='pk', receivers=None, receiver_fnc=None, receiver_args=[], receiver_kwargs={}, notification_context={}):
    """
    Send out an notification
    """

    # Set defaults
    if not entry_name:
        entry_name = obj._meta.modelname

    # Resolve objekt reference
    obj_ref_value = getattr(obj, obj_ref)
    # Try with some defaults
    if not obj_ref_value:
        obj_ref_value = getattr(obj, 'pk')
    if not obj_ref_value:
        obj_ref_value = getattr(obj, 'id')
    if not obj_ref_value:
        raise KeyError(f"Could not resolve an object reference for '{str(obj)}' with {obj_ref}, pk, id")

    # Check if we have notified recently...
    delta = timedelta(days=1)

    if NotificationEntry.check_recent(entry_name, obj_ref_value, delta):
        logger.info(f"Notification '{entry_name}' has recently been sent for '{str(obj)}' - SKIPPING")
        return

    logger.info(f"Gathering users for notification '{entry_name}'")
    # Collect possible receivers
    if not receivers:
        receivers = receiver_fnc(*receiver_args, **receiver_kwargs)

    if receivers:
        logger.info(f"Sending notification '{entry_name}' for '{str(obj)}'")

        # Collect possible methods
        delivery_methods = inheritors(NotificationMethod)

        # TODO remove -> this is for debugging the delivery method runfs
        if settings.TESTING:
            print(delivery_methods)

        for method in [a for a in delivery_methods if a not in [SingleNotificationMethod, BulkNotificationMethod]]:
            logger.info(f"Triggering method '{method.METHOD_NAME}'")
            try:
                deliver_notification(method, obj, entry_name, receivers, notification_context)
            except NotImplementedError as error:
                print('NotImplementedError')
                raise error
            except Exception as error:
                print(error)
                logger.error(error)

        # Set delivery flag
        NotificationEntry.notify(entry_name, obj_ref_value)
    else:
        logger.info(f"No possible users for notification '{entry_name}'")


def deliver_notification(cls: NotificationMethod, obj, entry_name: str, receivers, notification_context: dict):
    # Init delivery method
    method = cls(obj, entry_name, receivers)

    if method.recipients and method.recipients.count() > 0:
        # Log start
        logger.info(f"Notify users via '{method.METHOD_NAME}' for notification '{entry_name}' for '{str(obj)}'")

        # Run setup for delivery method
        method.setup()

        success = True
        success_count = 0

        # Select delivery method and execute it
        if hasattr(method, 'send_bulk'):
            success = method.send_bulk(notification_context)
            success_count = method.recipients.count()

        elif hasattr(method, 'send'):
            for rec in method.recipients:
                if method.send(rec, notification_context):
                    success_count += 1
                else:
                    success = False

        else:
            raise NotImplementedError('No delivery method found')

        # Run cleanup for delivery method
        method.cleanup()

        # Log results
        logger.info(f"Notified {success_count} users via '{method.METHOD_NAME}' for notification '{entry_name}' for '{str(obj)}' successfully")
        if not success:
            logger.info("There were some problems")
