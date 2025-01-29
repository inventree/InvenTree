"""Base classes and functions for notifications."""

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

import structlog

import common.models
import InvenTree.helpers
from InvenTree.ready import isImportingData, isRebuildingData
from plugin import registry
from plugin.models import NotificationUserSetting, PluginConfig
from users.models import Owner

logger = structlog.get_logger('inventree')


# region methods
class NotificationMethod:
    """Base class for notification methods."""

    METHOD_NAME = ''
    METHOD_ICON = None
    CONTEXT_BUILTIN = ['name', 'message']
    CONTEXT_EXTRA = []
    GLOBAL_SETTING = None
    USER_SETTING = None

    def __init__(self, obj, category, targets, context) -> None:
        """Check that the method is read.

        This checks that:
        - All needed functions are implemented
        - The method is not disabled via plugin
        - All needed context values were provided
        """
        # Check if a sending fnc is defined
        if (not hasattr(self, 'send')) and (not hasattr(self, 'send_bulk')):
            raise NotImplementedError(
                'A NotificationMethod must either define a `send` or a `send_bulk` method'
            )

        # No method name is no good
        if self.METHOD_NAME in ('', None):
            raise NotImplementedError(
                f'The NotificationMethod {self.__class__} did not provide a METHOD_NAME'
            )

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
            # the obj is not accessible so we are on the end
            if not isinstance(obj, (list, dict, tuple)):
                return ref

            # check if the ref exists
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
            raise NotImplementedError(
                'This type can not be used as a context reference'
            )

        missing = []
        for item in (*self.CONTEXT_BUILTIN, *self.CONTEXT_EXTRA):
            ret = check(item, context)
            if ret:
                missing.append(ret)

        if missing:
            raise NotImplementedError(
                f'The `context` is missing the following items:\n{missing}'
            )

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
        plg_instance = registry.get_plugin(plg_cls.NAME.lower())
        return plg_instance and not plg_instance.get_setting(self.GLOBAL_SETTING)

    def usersetting(self, target):
        """Returns setting for this method for a given user."""
        return NotificationUserSetting.get_setting(
            f'NOTIFICATION_METHOD_{self.METHOD_NAME.upper()}',
            user=target,
            method=self.METHOD_NAME,
        )

    # endregion


class SingleNotificationMethod(NotificationMethod):
    """NotificationMethod that sends notifications one by one."""

    def send(self, target):
        """This function must be overridden."""
        raise NotImplementedError('The `send` method must be overridden!')


class BulkNotificationMethod(NotificationMethod):
    """NotificationMethod that sends all notifications in bulk."""

    def send_bulk(self):
        """This function must be overridden."""
        raise NotImplementedError('The `send` method must be overridden!')


# endregion


class MethodStorageClass:
    """Class that works as registry for all available notification methods in InvenTree.

    Is initialized on startup as one instance named `storage` in this file.
    """

    methods_list = None
    user_settings = {}

    @property
    def methods(self):
        """Return all available methods.

        This is cached, and stored internally.
        """
        if self.methods_list is None:
            self.collect()

        return self.methods_list

    def collect(self, selected_classes=None):
        """Collect all classes in the environment that are notification methods.

        Can be filtered to only include provided classes for testing.

        Args:
            selected_classes (class, optional): References to the classes that should be registered. Defaults to None.
        """
        logger.debug('Collecting notification methods...')

        current_method = (
            InvenTree.helpers.inheritors(NotificationMethod) - IGNORED_NOTIFICATION_CLS
        )

        # for testing selective loading is made available
        if selected_classes:
            current_method = [
                item for item in current_method if item is selected_classes
            ]

        # make sure only one of each method is added
        filtered_list = {}
        for item in current_method:
            plugin = item.get_plugin(item)
            ref = (
                f'{plugin.package_path}_{item.METHOD_NAME}'
                if plugin
                else item.METHOD_NAME
            )
            item.plugin = plugin() if plugin else None
            filtered_list[ref] = item

        storage.methods_list = list(filtered_list.values())

        logger.info('Found %s notification methods', len(storage.methods_list))

        for item in storage.methods_list:
            logger.debug(' - %s', str(item))

    def get_usersettings(self, user) -> list:
        """Returns all user settings for a specific user.

        This is needed to show them in the settings UI.

        Args:
            user (User): User that should be used as a filter.

        Returns:
            list: All applicablae notification settings.
        """
        methods = []

        for item in storage.methods:
            if item.USER_SETTING:
                new_key = f'NOTIFICATION_METHOD_{item.METHOD_NAME.upper()}'

                # make sure the setting exists
                self.user_settings[new_key] = item.USER_SETTING
                NotificationUserSetting.get_setting(
                    key=new_key, user=user, method=item.METHOD_NAME
                )

                # save definition
                methods.append({
                    'key': new_key,
                    'icon': getattr(item, 'METHOD_ICON', ''),
                    'method': item.METHOD_NAME,
                })

        return methods


IGNORED_NOTIFICATION_CLS = {SingleNotificationMethod, BulkNotificationMethod}
storage = MethodStorageClass()


class UIMessageNotification(SingleNotificationMethod):
    """Delivery method for sending specific users notifications in the notification pain in the web UI."""

    METHOD_NAME = 'ui_message'

    def get_targets(self):
        """Only send notifications for active users."""
        return [target for target in self.targets if target.is_active]

    def send(self, target):
        """Send a UI notification to a user."""
        common.models.NotificationMessage.objects.create(
            target_object=self.obj,
            source_object=target,
            user=target,
            category=self.category,
            name=self.context['name'],
            message=self.context['message'],
        )
        return True


@dataclass()
class NotificationBody:
    """Information needed to create a notification.

    Attributes:
        name (str): Name (or subject) of the notification
        slug (str): Slugified reference for notification
        message (str): Notification message as text. Should not be longer than 120 chars.
        template (str): Reference to the html template for the notification.

    The strings support f-string style formatting with context variables parsed at runtime.

    Context variables:
        instance: Text representing the instance
        verbose_name: Verbose name of the model
        app_label: App label (slugified) of the model
        model_name': Name (slugified) of the model
    """

    name: str
    slug: str
    message: str
    template: Optional[str] = None


class InvenTreeNotificationBodies:
    """Default set of notifications for InvenTree.

    Contains regularly used notification bodies.
    """

    NewOrder = NotificationBody(
        name=_('New {verbose_name}'),
        slug='{app_label}.new_{model_name}',
        message=_('A new order has been created and assigned to you'),
        template='email/new_order_assigned.html',
    )
    """Send when a new order (build, sale or purchase) was created."""

    OrderCanceled = NotificationBody(
        name=_('{verbose_name} canceled'),
        slug='{app_label}.canceled_{model_name}',
        message=_('A order that is assigned to you was canceled'),
        template='email/canceled_order_assigned.html',
    )
    """Send when a order (sale, return or purchase) was canceled."""

    ItemsReceived = NotificationBody(
        name=_('Items Received'),
        slug='purchase_order.items_received',
        message=_('Items have been received against a purchase order'),
        template='email/purchase_order_received.html',
    )

    ReturnOrderItemsReceived = NotificationBody(
        name=_('Items Received'),
        slug='return_order.items_received',
        message=_('Items have been received against a return order'),
        template='email/return_order_received.html',
    )


def trigger_notification(obj, category=None, obj_ref='pk', **kwargs):
    """Send out a notification."""
    targets = kwargs.get('targets')
    target_fnc = kwargs.get('target_fnc')
    target_args = kwargs.get('target_args', [])
    target_kwargs = kwargs.get('target_kwargs', {})
    target_exclude = kwargs.get('target_exclude')
    context = kwargs.get('context', {})
    delivery_methods = kwargs.get('delivery_methods')

    # Check if data is importing currently
    if isImportingData() or isRebuildingData():
        return

    # Resolve object reference
    refs = [obj_ref, 'pk', 'id', 'uid']

    obj_ref_value = None

    # Find the first reference that is available
    for ref in refs:
        if hasattr(obj, ref):
            obj_ref_value = getattr(obj, ref)
            break

    # Try with some defaults
    if not obj_ref_value:
        raise KeyError(
            f"Could not resolve an object reference for '{obj!s}' with {','.join(set(refs))}"
        )

    # Check if we have notified recently...
    delta = timedelta(days=1)

    if common.models.NotificationEntry.check_recent(category, obj_ref_value, delta):
        logger.info(
            "Notification '%s' has recently been sent for '%s' - SKIPPING",
            category,
            str(obj),
        )
        return

    logger.info("Gathering users for notification '%s'", category)

    if target_exclude is None:
        target_exclude = set()

    # Collect possible targets
    if not targets:
        targets = target_fnc(*target_args, **target_kwargs)

    # Convert list of targets to a list of users
    # (targets may include 'owner' or 'group' classes)
    target_users = set()

    if targets:
        for target in targets:
            if target is None:
                continue
            # User instance is provided
            elif isinstance(target, get_user_model()):
                if target not in target_exclude:
                    target_users.add(target)
            # Group instance is provided
            elif isinstance(target, Group):
                for user in get_user_model().objects.filter(groups__name=target.name):
                    if user not in target_exclude:
                        target_users.add(user)
            # Owner instance (either 'user' or 'group' is provided)
            elif isinstance(target, Owner):
                for owner in target.get_related_owners(include_group=False):
                    user = owner.owner
                    if user not in target_exclude:
                        target_users.add(user)
            # Unhandled type
            else:
                logger.error(
                    'Unknown target passed to trigger_notification method: %s', target
                )

    if target_users:
        logger.info("Sending notification '%s' for '%s'", category, str(obj))

        # Collect possible methods
        if delivery_methods is None:
            delivery_methods = storage.methods or []
        else:
            delivery_methods = delivery_methods - IGNORED_NOTIFICATION_CLS

        for method in delivery_methods:
            logger.info("Triggering notification method '%s'", method.METHOD_NAME)
            try:
                deliver_notification(method, obj, category, target_users, context)
            except NotImplementedError as error:
                # Allow any single notification method to fail, without failing the others
                logger.error(error)
            except Exception as error:
                logger.error(error)

        # Set delivery flag
        common.models.NotificationEntry.notify(category, obj_ref_value)
    else:
        logger.info("No possible users for notification '%s'", category)


def trigger_superuser_notification(plugin: PluginConfig, msg: str):
    """Trigger a notification to all superusers.

    Args:
        plugin (PluginConfig): Plugin that is raising the notification
        msg (str): Detailed message that should be attached
    """
    users = get_user_model().objects.filter(is_superuser=True)

    trigger_notification(
        plugin,
        'inventree.plugin',
        context={'error': plugin, 'name': _('Error raised by plugin'), 'message': msg},
        targets=users,
        delivery_methods={UIMessageNotification},
    )


def deliver_notification(
    cls: NotificationMethod, obj, category: str, targets, context: dict
):
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
        logger.info(
            "Notify users via '%s' for notification '%s' for '%s'",
            method.METHOD_NAME,
            category,
            str(obj),
        )

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
        logger.info(
            "Notified %s users via '%s' for notification '%s' for '%s' successfully",
            success_count,
            method.METHOD_NAME,
            category,
            str(obj),
        )
        if not success:
            logger.info('There were some problems')
