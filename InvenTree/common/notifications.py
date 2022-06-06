"""Base classes and functions for notifications."""

import logging
from datetime import timedelta

from common.models import NotificationEntry, NotificationMessage
from InvenTree.helpers import inheritors
from InvenTree.ready import isImportingData
from plugin import registry
from plugin.models import NotificationUserSetting

logger = logging.getLogger('inventree')


# region methods
class NotificationMethod:
    """Base class for notification methods."""

    METHOD_NAME = ''
    METHOD_ICON = None
    CONTEXT_BUILTIN = ['name', 'message', ]
    CONTEXT_EXTRA = []
    GLOBAL_SETTING = None
    USER_SETTING = None

    def __init__(self, obj, category, targets, context) -> None:
        """Check that the method is read.

        This checks that:
        - All needed functions are implemented
        - The method is not disabled via plugin
        - All needed contaxt values were provided
        """
        # Check if a sending fnc is defined
        if (not hasattr(self, 'send')) and (not hasattr(self, 'send_bulk')):
            raise NotImplementedError('A NotificationMethod must either define a `send` or a `send_bulk` method')

        # No method name is no good
        if self.METHOD_NAME in ('', None):
            raise NotImplementedError(f'The NotificationMethod {self.__class__} did not provide a METHOD_NAME')

        # Check if plugin is disabled - if so do not gather targets etc.
        if self.global_setting_disable():
            self.targets = None
            return

        # Define arguments
        self.obj = obj
        self.category = category
        self.targets = targets
        self.context = self.check_context(context)

        # Gather targets
        self.targets = self.get_targets()

    def check_context(self, context):
        """Check that all values defined in the methods CONTEXT were provided in the current context."""
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
        """Returns targets for notifications.

        Processes `self.targets` to extract all users that should be notified.
        """
        raise NotImplementedError('The `get_targets` method must be implemented!')

    def setup(self):
        """Set up context before notifications are send.

        This is intended to be overridden in method implementations.
        """
        return True

    def cleanup(self):
        """Clean up context after all notifications were send.

        This is intended to be overridden in method implementations.
        """
        return True

    # region plugins
    def get_plugin(self):
        """Returns plugin class."""
        return False

    def global_setting_disable(self):
        """Check if the method is defined in a plugin and has a global setting."""
        # Check if plugin has a setting
        if not self.GLOBAL_SETTING:
            return False

        # Check if plugin is set
        plg_cls = self.get_plugin()
        if not plg_cls:
            return False

        # Check if method globally enabled
        plg_instance = registry.plugins.get(plg_cls.NAME.lower())
        if plg_instance and not plg_instance.get_setting(self.GLOBAL_SETTING):
            return True

        # Lets go!
        return False

    def usersetting(self, target):
        """Returns setting for this method for a given user."""
        return NotificationUserSetting.get_setting(f'NOTIFICATION_METHOD_{self.METHOD_NAME.upper()}', user=target, method=self.METHOD_NAME)
    # endregion


class SingleNotificationMethod(NotificationMethod):
    """NotificationMethod that sends notifications one by one."""

    def send(self, target):
        """This function must be overriden."""
        raise NotImplementedError('The `send` method must be overriden!')


class BulkNotificationMethod(NotificationMethod):
    """NotificationMethod that sends all notifications in bulk."""

    def send_bulk(self):
        """This function must be overriden."""
        raise NotImplementedError('The `send` method must be overriden!')
# endregion


class MethodStorageClass:
    """Class that works as registry for all available notification methods in InvenTree.

    Is initialized on startup as one instance named `storage` in this file.
    """

    liste = None
    user_settings = {}

    def collect(self, selected_classes=None):
        """Collect all classes in the enviroment that are notification methods.

        Can be filtered to only include provided classes for testing.

        Args:
            selected_classes (class, optional): References to the classes that should be registered. Defaults to None.
        """
        logger.info('collecting notification methods')
        current_method = inheritors(NotificationMethod) - IGNORED_NOTIFICATION_CLS

        # for testing selective loading is made available
        if selected_classes:
            current_method = [item for item in current_method if item is selected_classes]

        # make sure only one of each method is added
        filtered_list = {}
        for item in current_method:
            plugin = item.get_plugin(item)
            ref = f'{plugin.package_path}_{item.METHOD_NAME}' if plugin else item.METHOD_NAME
            filtered_list[ref] = item

        storage.liste = list(filtered_list.values())
        logger.info(f'found {len(storage.liste)} notification methods')

    def get_usersettings(self, user) -> list:
        """Returns all user settings for a specific user.

        This is needed to show them in the settings UI.

        Args:
            user (User): User that should be used as a filter.

        Returns:
            list: All applicablae notification settings.
        """
        methods = []
        for item in storage.liste:
            if item.USER_SETTING:
                new_key = f'NOTIFICATION_METHOD_{item.METHOD_NAME.upper()}'

                # make sure the setting exists
                self.user_settings[new_key] = item.USER_SETTING
                NotificationUserSetting.get_setting(
                    key=new_key,
                    user=user,
                    method=item.METHOD_NAME,
                )

                # save definition
                methods.append({
                    'key': new_key,
                    'icon': getattr(item, 'METHOD_ICON', ''),
                    'method': item.METHOD_NAME,
                })
        return methods


IGNORED_NOTIFICATION_CLS = set([
    SingleNotificationMethod,
    BulkNotificationMethod,
])
storage = MethodStorageClass()


class UIMessageNotification(SingleNotificationMethod):
    """Delivery method for sending specific users notifications in the notification pain in the web UI."""

    METHOD_NAME = 'ui_message'

    def get_targets(self):
        """Just return the targets - no tricks here."""
        return self.targets

    def send(self, target):
        """Send a UI notification to a user."""
        NotificationMessage.objects.create(
            target_object=self.obj,
            source_object=target,
            user=target,
            category=self.category,
            name=self.context['name'],
            message=self.context['message'],
        )
        return True


def trigger_notification(obj, category=None, obj_ref='pk', **kwargs):
    """Send out a notification."""
    targets = kwargs.get('targets', None)
    target_fnc = kwargs.get('target_fnc', None)
    target_args = kwargs.get('target_args', [])
    target_kwargs = kwargs.get('target_kwargs', {})
    context = kwargs.get('context', {})
    delivery_methods = kwargs.get('delivery_methods', None)

    # Check if data is importing currently
    if isImportingData():
        return

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
        if delivery_methods is None:
            delivery_methods = storage.liste
        else:
            delivery_methods = (delivery_methods - IGNORED_NOTIFICATION_CLS)

        for method in delivery_methods:
            logger.info(f"Triggering notification method '{method.METHOD_NAME}'")
            try:
                deliver_notification(method, obj, category, targets, context)
            except NotImplementedError as error:
                # Allow any single notification method to fail, without failing the others
                logger.error(error)
            except Exception as error:
                logger.error(error)

        # Set delivery flag
        NotificationEntry.notify(category, obj_ref_value)
    else:
        logger.info(f"No possible users for notification '{category}'")


def deliver_notification(cls: NotificationMethod, obj, category: str, targets, context: dict):
    """Send notification with the provided class.

    This:
    - Intis the method
    - Checks that there are valid targets
    - Runs the delivery setup
    - Sends notifications either via `send_bulk` or send`
    - Runs the delivery cleanup
    """
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
