"""Functions for processing emails."""

from typing import Union

from django.core.mail.message import EmailMessage, EmailMultiAlternatives

from common.settings import get_global_setting
from InvenTree.backends import logger
from plugin.plugin import PluginMixinEnum
from plugin.registry import registry


def process_mail(
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
