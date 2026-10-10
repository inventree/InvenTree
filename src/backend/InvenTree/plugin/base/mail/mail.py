"""Functions for processing emails."""

from typing import Optional

from django.core.mail.message import EmailMessage, EmailMultiAlternatives

from common.models import EmailMessage as InventreeEmailMessage
from common.settings import get_global_setting
from InvenTree.backends import logger
from plugin.plugin import PluginMixinEnum
from plugin.registry import registry


def process_mail_out(
    email_messages: list[EmailMessage | EmailMultiAlternatives],
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

    # Ensure messages are a list
    if not isinstance(email_messages, list):
        email_messages = [email_messages]

    for plugin in registry.with_mixin(PluginMixinEnum.MAIL):
        for message in email_messages:
            try:
                plugin.process_mail_out(message)
            except Exception:  # pragma: no cover
                logger.exception(
                    'Exception during mail processing for plugin %s', plugin.slug
                )
    return True


def process_mail_in(
    email_message: Optional[InventreeEmailMessage] = None, mail_id: Optional[int] = None
) -> bool:
    """Process an incoming email message with plugins.

    Args:
        email_message (Optional[InventreeEmailMessage]): The email message to process.
        mail_id (int): The ID of the email message to process if email_message is None. This is required if running through the tasks framework.

    Returns:
        bool: True if processing was successful, False otherwise.
    """
    if not get_global_setting('ENABLE_PLUGINS_MAILS', False):
        # Do nothing if plugin mails are not enabled
        return False

    if email_message is None:
        if mail_id is None:
            logger.error('No email message or mail ID provided for processing')
            return False
        try:
            email_message = InventreeEmailMessage.objects.get(id=mail_id)
        except InventreeEmailMessage.DoesNotExist:
            logger.error('Email message with ID %s does not exist', mail_id)
            return False

    for plugin in registry.with_mixin(PluginMixinEnum.MAIL):
        try:
            plugin.process_mail_in(email_message)
        except Exception:  # pragma: no cover
            logger.exception(
                'Exception during mail processing for plugin %s', plugin.slug
            )
    return True
