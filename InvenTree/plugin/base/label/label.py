"""Functions to print a label to a mixin printer"""
import logging
import sys
import traceback

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.views.debug import ExceptionReporter

from error_report.models import Error

import common.notifications
from plugin.registry import registry

logger = logging.getLogger('inventree')


def print_label(plugin_slug, pdf_data, filename=None, label_instance=None, user=None):
    """
    Print label with the provided plugin.

    This task is nominally handled by the background worker.

    If the printing fails (throws an exception) then the user is notified.

    Arguments:
        plugin_slug: The unique slug (key) of the plugin
        pdf_data: Binary PDF data
        filename: The intended name of the printed label
    """

    logger.info(f"Plugin '{plugin_slug}' is printing a label '{filename}'")

    plugin = registry.plugins.get(plugin_slug, None)

    if plugin is None:  # pragma: no cover
        logger.error(f"Could not find matching plugin for '{plugin_slug}'")
        return

    try:
        plugin.print_label(
            pdf_data,
            filename=filename,
            label_instance=label_instance,
            width=label_instance.width,
            height=label_instance.height,
            user=user
        )
    except Exception as e:  # pragma: no cover
        # Plugin threw an error - notify the user who attempted to print

        ctx = {
            'name': _('Label printing failed'),
            'message': str(e),
        }

        # Log an error message to the database
        kind, info, data = sys.exc_info()

        Error.objects.create(
            kind=kind.__name__,
            info=info,
            data='\n'.join(traceback.format_exception(kind, info, data)),
            path='print_label',
            html=ExceptionReporter(None, kind, info, data).get_traceback_html(),
        )

        logger.error(f"Label printing failed: Sending notification to user '{user}'")  # pragma: no cover

        # Throw an error against the plugin instance
        common.notifications.trigger_notification(
            plugin.plugin_config(),
            'label.printing_failed',
            targets=[user],
            context=ctx,
            delivery_methods=set([common.notifications.UIMessageNotification])
        )

        if settings.TESTING:
            # If we are in testing mode, we want to know about this exception
            raise e
