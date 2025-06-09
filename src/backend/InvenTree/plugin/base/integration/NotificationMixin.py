"""Plugin mixin class for supporting third-party notification methods."""

from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db.models import Model

import structlog

from plugin import PluginMixinEnum

logger = structlog.get_logger('inventree')

if TYPE_CHECKING:
    from common.models import SettingsKeyType
else:

    class SettingsKeyType:
        """Dummy class, so that python throws no error."""


class NotificationMixin:
    """Plugin mixin class for supporting third-party notification methods."""

    class MixinMeta:
        """Meta for mixin."""

        MIXIN_NAME = PluginMixinEnum.NOTIFICATION

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin(PluginMixinEnum.NOTIFICATION, True, __class__)

    def filter_targets(self, targets: list[User]) -> list[User]:
        """Filter notification targets based on the plugin's logic."""
        # Default implementation returns all targets
        return targets

    def send_notification(
        self, target: Model, category: str, users: list, context: dict
    ) -> None:
        """Send notification to the specified target users.

        Arguments:
            target (Model): The target model instance to which the notification relates.
            category (str): The category of the notification.
            users (list): List of users to send the notification to.
            context (dict): Context data for the notification.
        """
        # The default implementation does nothing
