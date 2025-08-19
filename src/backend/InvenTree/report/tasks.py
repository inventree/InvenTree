"""Background tasks for the report app."""

import structlog
from opentelemetry import trace

from InvenTree.exceptions import log_error

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger('inventree')


@tracer.start_as_current_span('print_reports')
def print_reports(template_id: int, item_ids: list[int], output_id: int, **kwargs):
    """Print multiple reports against the provided template.

    Arguments:
        template_id: The ID of the ReportTemplate to use
        item_ids: List of item IDs to generate the report against
        output_id: The ID of the DataOutput to use (if provided)

    This function is intended to be called by the background worker,
    and will continuously update the status of the DataOutput object.
    """
    from common.models import DataOutput
    from report.models import ReportTemplate

    try:
        template = ReportTemplate.objects.get(pk=template_id)
        output = DataOutput.objects.get(pk=output_id)
    except Exception:
        log_error('report.tasks.print_reports')
        return

    # Fetch the items to be included in the report
    model = template.get_model()
    items = model.objects.filter(pk__in=item_ids)

    template.print(items, output=output)


@tracer.start_as_current_span('print_labels')
def print_labels(
    template_id: int, item_ids: list[int], output_id: int, plugin_slug: str, **kwargs
):
    """Print multiple labels against the provided template.

    Arguments:
        template_id: The ID of the LabelTemplate to use
        item_ids: List of item IDs to generate the labels against
        output_id: The ID of the DataOutput to use (if provided)
        plugin_slug: The ID of the LabelPlugin to use (if provided)

    This function is intended to be called by the background worker,
    and will continuously update the status of the DataOutput object.
    """
    from common.models import DataOutput
    from plugin.registry import registry
    from report.models import LabelTemplate

    try:
        template = LabelTemplate.objects.get(pk=template_id)
        output = DataOutput.objects.get(pk=output_id)
    except Exception:
        log_error('report.tasks.print_labels')
        return

    # Fetch the items to be included in the report
    model = template.get_model()
    items = model.objects.filter(pk__in=item_ids)

    # Ensure they are sorted by the order of the provided item IDs
    items = sorted(items, key=lambda item: item_ids.index(item.pk))

    plugin = registry.get_plugin(plugin_slug, active=True)

    if not plugin:
        logger.warning("Label printing plugin '%s' not found", plugin_slug)
        return

    # Extract optional arguments for label printing
    options = kwargs.pop('options') or {}

    template.print(items, plugin, output=output, options=options)
