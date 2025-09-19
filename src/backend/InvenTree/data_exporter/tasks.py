"""Background tasks for the exporting app."""

from django.contrib.auth.models import User
from django.test.client import RequestFactory

import structlog

from common.models import DataOutput

logger = structlog.get_logger('inventree')


def export_data(
    view_class,
    user_id: int,
    query_params: dict,
    plugin_key: str,
    export_format: str,
    export_context: dict,
    output_id: int,
):
    """Perform the data export task using the provided parameters.

    Arguments:
        view_class: The class of the view to export data from
        user_id: The ID of the user who requested the export
        query_params: Query parameters for the export
        plugin_key: The key for the export plugin
        export_format: The output format for the export
        export_context: Additional options for the export
        output_id: The ID of the DataOutput instance to write to

    This function is designed to be called by the background task,
    to avoid blocking the web server.
    """
    from plugin import registry

    if (plugin := registry.get_plugin(plugin_key, active=True)) is None:
        logger.warning("export_data: Plugin '%s' not found", plugin_key)
        return

    if (user := User.objects.filter(pk=user_id).first()) is None:
        logger.warning('export_data: User not found: %d', user_id)
        return

    if (output := DataOutput.objects.filter(pk=output_id).first()) is None:
        logger.warning('export_data: Output object not found: %d', output_id)
        return

    # Recreate the request object - this is required for the view to function correctly
    # Note that the request object cannot be pickled, so we need to recreate it here
    request = RequestFactory()
    request.user = user
    request.query_params = query_params

    view = view_class()
    view.request = request
    view.args = getattr(view, 'args', ())
    view.kwargs = getattr(view, 'kwargs', {})
    view.format_kwarg = getattr(view, 'format_kwarg', None)

    view.export_data(plugin, export_format, export_context, output)
