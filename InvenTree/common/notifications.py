import logging
from datetime import timedelta

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
    CONTEXT_BUILTIN = ['name', 'message', ]
    CONTEXT_EXTRA = []

    def __init__(self, obj, category, targets, context) -> None:
        # Check if a sending fnc is defined
        if (not hasattr(self, 'send')) and (not hasattr(self, 'send_bulk')):
            raise NotImplementedError('A NotificationMethod must either define a `send` or a `send_bulk` method')

        # No method name is no good
        if self.METHOD_NAME in ('', None):
            raise NotImplementedError(f'The NotificationMethod {self.__class__} did not provide a METHOD_NAME')

        # Define arguments
        self.obj = obj
        self.category = category
        self.targets = targets
        self.context = self.check_context(context)

        # Gather targets
        self.targets = self.get_targets()

    def check_context(self, context):
        def check(ref, obj):
            # the obj is not accesible so we are on the end
            if not isinstance(obj, (list, dict, tuple, )):
                return ref

            # check if the ref exsists
            if isinstance(ref, str):
                if not obj.get(ref):
                    return ref
                return False

            # nested
            elif isinstance(ref, (tuple, list)):
                if len(ref) == 1:
                    return check(ref[0], obj)
                ret = check(ref[0], obj)
                if ret:
                    return ret
                return check(ref[1:], obj[ref[0]])

            # other cases -> raise
            raise NotImplementedError('This type can not be used as a context reference')

        missing = []
        for item in (*self.CONTEXT_BUILTIN, *self.CONTEXT_EXTRA):
            ret = check(item, context)
            if ret:
                missing.append(ret)

        if missing:
            raise NotImplementedError(f'The `context` is missing the following items:\n{missing}')

        return context

    def get_targets(self):
        raise NotImplementedError('The `get_targets` method must be implemented!')

    def setup(self):
        return True

    # def send(self, targets)
    # def send_bulk(self)

    def cleanup(self):
        return True


class SingleNotificationMethod(NotificationMethod):
    def send(self, target):
        raise NotImplementedError('The `send` method must be overriden!')


class BulkNotificationMethod(NotificationMethod):
    def send_bulk(self):
        raise NotImplementedError('The `send` method must be overriden!')
# endregion


# region implementations
class EmailNotification(BulkNotificationMethod):
    METHOD_NAME = 'mail'
    CONTEXT_EXTRA = [
        ('template', ),
        ('template', 'html', ),
        ('template', 'subject', ),
    ]

    def get_targets(self):
        return EmailAddress.objects.filter(
            user__in=self.targets,
        )

    def send_bulk(self):
        html_message = render_to_string(self.context['template']['html'], self.context)
        targets = self.targets.values_list('email', flat=True)

        InvenTree.tasks.send_email(self.context['template']['subject'], '', targets, html_message=html_message)

        return True


class UIMessageNotification(SingleNotificationMethod):
    METHOD_NAME = 'ui_message'

    def get_targets(self):
        return self.targets

    def send(self, target):
        NotificationMessage.objects.create(
            target_object=self.obj,
            source_object=target,
            user=target,
            category=self.category,
            name=self.context['name'],
            message=self.context['message'],
        )
        return True
# endregion
# endregion


def trigger_notifaction(obj, category=None, obj_ref='pk', targets=None, target_fnc=None, target_args=[], target_kwargs={}, context={}):
    """
    Send out an notification
    """
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

    if NotificationEntry.check_recent(category, obj_ref_value, delta):
        logger.info(f"Notification '{category}' has recently been sent for '{str(obj)}' - SKIPPING")
        return

    logger.info(f"Gathering users for notification '{category}'")
    # Collect possible targets
    if not targets:
        targets = target_fnc(*target_args, **target_kwargs)

    if targets:
        logger.info(f"Sending notification '{category}' for '{str(obj)}'")

        # Collect possible methods
        delivery_methods = inheritors(NotificationMethod)

        for method in [a for a in delivery_methods if a not in [SingleNotificationMethod, BulkNotificationMethod]]:
            logger.info(f"Triggering method '{method.METHOD_NAME}'")
            try:
                deliver_notification(method, obj, category, targets, context)
            except NotImplementedError as error:
                raise error
            except Exception as error:
                logger.error(error)

        # Set delivery flag
        NotificationEntry.notify(category, obj_ref_value)
    else:
        logger.info(f"No possible users for notification '{category}'")


def deliver_notification(cls: NotificationMethod, obj, category: str, targets, context: dict):
    # Init delivery method
    method = cls(obj, category, targets, context)

    if method.targets and len(method.targets) > 0:
        # Log start
        logger.info(f"Notify users via '{method.METHOD_NAME}' for notification '{category}' for '{str(obj)}'")

        # Run setup for delivery method
        method.setup()

        # Counters for success logs
        success = True
        success_count = 0

        # Select delivery method and execute it
        if hasattr(method, 'send_bulk'):
            success = method.send_bulk()
            success_count = len(method.targets)

        elif hasattr(method, 'send'):
            for target in method.targets:
                if method.send(target):
                    success_count += 1
                else:
                    success = False

        # Run cleanup for delivery method
        method.cleanup()

        # Log results
        logger.info(f"Notified {success_count} users via '{method.METHOD_NAME}' for notification '{category}' for '{str(obj)}' successfully")
        if not success:
            logger.info("There were some problems")
