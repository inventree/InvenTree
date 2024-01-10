"""Functions to print a label to a mixin printer."""

import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _

import common.notifications

from InvenTree.exceptions import log_error
from plugin.registry import registry

logger = logging.getLogger('inventree')


def print_label(plugin_slug: str, **kwargs):
    """Print label with the provided plugin.

    This task is nominally handled by the background worker.
    If the printing fails (throws an exception) then the user is notified.

    Arguments:
        plugin_slug (str): The unique slug (key) of the plugin.

    kwargs:
        passed through to the plugin.print_label() method
    """
    logger.info("Plugin '%s' is printing a label", plugin_slug)

    plugin = registry.get_plugin(plugin_slug)

    if plugin is None:  # pragma: no cover
        logger.error("Could not find matching plugin for '%s'", plugin_slug)
        return

    try:
        plugin.print_label(**kwargs)
    except Exception as e:  # pragma: no cover
        # Plugin threw an error - notify the user who attempted to print
        ctx = {'name': _('Label printing failed'), 'message': str(e)}

        user = kwargs.get('user', None)

        if user:
            # Log an error message to the database
            log_error('plugin.print_label')
            logger.exception(
                "Label printing failed: Sending notification to user '%s'", user
            )  # pragma: no cover

            # Throw an error against the plugin instance
            common.notifications.trigger_notification(
                plugin.plugin_config(),
                'label.printing_failed',
                targets=[user],
                context=ctx,
                delivery_methods={common.notifications.UIMessageNotification},
            )

        if settings.TESTING:
            # If we are in testing mode, we want to know about this exception
            raise e
