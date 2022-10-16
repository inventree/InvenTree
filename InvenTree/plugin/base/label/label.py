"""Functions to print a label to a mixin printer."""

import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _

import pdf2image

import common.notifications
from common.models import InvenTreeSetting
from InvenTree.exceptions import log_error
from plugin.registry import registry

logger = logging.getLogger('inventree')


def print_label(plugin_slug: str, pdf_data, filename=None, label_instance=None, user=None):
    """Print label with the provided plugin.

    This task is nominally handled by the background worker.
    If the printing fails (throws an exception) then the user is notified.

    Args:
        plugin_slug (str): The unique slug (key) of the plugin.
        pdf_data: Binary PDF data.
        filename: The intended name of the printed label. Defaults to None.
        label_instance (Union[LabelTemplate, None], optional): The template instance that should be printed. Defaults to None.
        user (Union[User, None], optional): User that should be informed of errors. Defaults to None.
    """
    logger.info(f"Plugin '{plugin_slug}' is printing a label '{filename}'")

    plugin = registry.plugins.get(plugin_slug, None)

    if plugin is None:  # pragma: no cover
        logger.error(f"Could not find matching plugin for '{plugin_slug}'")
        return

    # In addition to providing a .pdf image, we'll also provide a .png file
    dpi = InvenTreeSetting.get_setting('LABEL_DPI', 300)
    png_file = pdf2image.convert_from_bytes(
        pdf_data,
        dpi=dpi,
    )[0]

    try:
        plugin.print_label(
            pdf_data=pdf_data,
            png_file=png_file,
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
        log_error('plugin.print_label')
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
