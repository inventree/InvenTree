"""Functions to print a label to a mixin printer"""
import logging

from django.utils.translation import gettext_lazy as _

import common.notifications
from plugin.registry import registry

logger = logging.getLogger('inventree')


def print_label(plugin_slug, label_image, label_instance=None, user=None):
    """
    Print label with the provided plugin.

    This task is nominally handled by the background worker.

    If the printing fails (throws an exception) then the user is notified.

    Arguments:
        plugin_slug: The unique slug (key) of the plugin
        label_image: A PIL.Image image object to be printed
    """

    logger.info(f"Plugin '{plugin_slug}' is printing a label")

    plugin = registry.plugins.get(plugin_slug, None)

    if plugin is None:
        logger.error(f"Could not find matching plugin for '{plugin_slug}'")
        return

    try:
        plugin.print_label(label_image, width=label_instance.width, height=label_instance.height)
    except Exception as e:
        # Plugin threw an error - notify the user who attempted to print

        ctx = {
            'name': _('Label printing failed'),
            'message': str(e),
        }

        logger.error(f"Label printing failed: Sending notification to user '{user}'")

        # Throw an error against the plugin instance
        common.notifications.trigger_notifaction(
            plugin.plugin_config(),
            'label.printing_failed',
            targets=[user],
            context=ctx,
            delivery_methods=[common.notifications.UIMessageNotification]
        )
