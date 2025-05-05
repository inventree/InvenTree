"""Custom backend implementation for maintenance-mode."""

import datetime
import time
from typing import Union

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage, EmailMultiAlternatives
from django.utils.module_loading import import_string

import structlog
from maintenance_mode.backends import AbstractStateBackend

import common.models
from common.settings import get_global_setting, set_global_setting
from plugin.plugin import PluginMixinEnum
from plugin.registry import registry

logger = structlog.get_logger('inventree')


class InvenTreeMaintenanceModeBackend(AbstractStateBackend):
    """Custom backend for managing state of maintenance mode.

    Stores a timestamp in the database to determine when maintenance mode will elapse.
    """

    SETTING_KEY = '_MAINTENANCE_MODE'

    def get_value(self) -> bool:
        """Get the current state of the maintenance mode.

        Returns:
            bool: True if maintenance mode is active, False otherwise.
        """
        try:
            value = get_global_setting(self.SETTING_KEY)
        except Exception:
            # Database is inaccessible - assume we are not in maintenance mode
            logger.debug('Failed to read maintenance mode state - assuming False')
            return False

        # Extract timestamp from string
        try:
            # If the timestamp is in the past, we are now *out* of maintenance mode
            timestamp = datetime.datetime.fromisoformat(value)
            return timestamp > datetime.datetime.now()
        except ValueError:
            # If the value is not a valid timestamp, assume maintenance mode is not active
            return False

    def set_value(self, value: bool, retries: int = 5, minutes: int = 5):
        """Set the state of the maintenance mode.

        Instead of simply writing "true" or "false" to the setting,
        we write a timestamp to the setting, which is used to determine
        when maintenance mode will elapse.
        This ensures that we will always *exit* maintenance mode after a certain time period.
        """
        logger.debug('Setting maintenance mode state: %s', value)

        if value:
            # Save as isoformat
            timestamp = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            timestamp = timestamp.isoformat()
        else:
            # Blank timestamp means maintenance mode is not active
            timestamp = ''

        r = retries

        while r > 0:
            try:
                set_global_setting(self.SETTING_KEY, timestamp)
                # Read the value back to confirm
                if self.get_value() == value:
                    break
            except Exception:
                # In the database is locked, then
                logger.debug(
                    'Failed to set maintenance mode state (%s retries left)', r
                )
                time.sleep(0.1)

            r -= 1

            if r == 0:
                logger.warning(
                    'Failed to set maintenance mode state after %s retries', retries
                )


class InvenTreeMailLoggingBackend(BaseEmailBackend):
    """Backend that logs send mails to the database."""

    def __init__(self, *args, **kwargs):
        """Initialize the email backend."""
        super().__init__(*args, **kwargs)
        klass = import_string(settings.INTERNAL_EMAIL_BACKEND)
        self.backend: BaseEmailBackend = klass(*args, **kwargs)

    def open(self):
        """Open the email backend connection."""
        return self.backend.open()

    def close(self):
        """Close the email backend connection."""
        return self.backend.open()

    def send_messages(
        self, email_messages: list[Union[EmailMessage, EmailMultiAlternatives]]
    ) -> int:
        """Send email messages and log them to the database.

        Args:
            email_messages (list): List of EmailMessage objects to send.
        """
        # Issue mails to plugins
        process_plugin_mail(email_messages)

        # Process
        msg_ids: list[common.models.EmailMessage] = []
        try:
            msg_ids = common.models.log_email_messages(email_messages)
        except Exception:  # pragma: no cover
            logger.exception('INVE-W9: Problem logging recipients, ignoring')

        # Send and log
        try:
            ret_val = self.backend.send_messages(email_messages)
            if ret_val == 0:
                logger.info('INVE-W9: No emails sent')
            else:
                logger.info('INVE-W9: %s emails sent', ret_val)
                common.models.EmailMessage.objects.filter(
                    pk__in=[msg.pk for msg in msg_ids]
                ).update(status=common.models.EmailMessage.EmailStatus.SENT)
            return ret_val
        except Exception:  # pragma: no cover
            logger.exception('INVE-W9: Exception during mail delivery')


def process_plugin_mail(
    email_messages: list[Union[EmailMessage, EmailMultiAlternatives]],
) -> bool:
    """Process email messages with plugins.

    Args:
        email_messages (list): List of EmailMessage objects to process.

    Returns:
        bool: True if processing was successful, False otherwise.
    """
    if not get_global_setting('ENABLE_PLUGINS_MAILS', False):
        # Do nothing if plugin mails are not enabled
        return False

    for plugin in registry.with_mixin(PluginMixinEnum.MAIL):
        for message in email_messages:
            try:
                plugin.process_mail(message)
            except Exception:
                logger.exception(
                    'Exception during mail processing for plugin %s', plugin.slug
                )
    return True
