"""Background tasks for the report app."""

from datetime import timedelta

import structlog

from InvenTree.exceptions import log_error
from InvenTree.helpers import current_time
from InvenTree.tasks import ScheduledTask, scheduled_task
from report.models import LabelOutput, ReportOutput

logger = structlog.get_logger('inventree')


@scheduled_task(ScheduledTask.DAILY)
def cleanup_old_report_outputs():
    """Remove old report/label outputs from the database."""
    # Remove any outputs which are older than 5 days
    threshold = current_time() - timedelta(days=5)

    LabelOutput.objects.filter(created__lte=threshold).delete()
    ReportOutput.objects.filter(created__lte=threshold).delete()


def print_reports(template_id: int, item_ids: list[int], output_id: int, **kwargs):
    """Print multiple reports against the provided template.

    Arguments:
        template_id: The ID of the ReportTemplate to use
        item_ids: List of item IDs to generate the report against
        output_id: The ID of the ReportOutput to use (if provided)

    This function is intended to be called by the background worker,
    and will continuously update the status of the ReportOutput object.
    """
    from report.models import ReportOutput, ReportTemplate

    try:
        template = ReportTemplate.objects.get(pk=template_id)
        output = ReportOutput.objects.get(pk=output_id)
    except Exception:
        log_error('report.tasks.print_reports')
        return

    # Fetch the items to be included in the report
    model = template.get_model()
    items = model.objects.filter(pk__in=item_ids)

    template.print(items, output=output)


def print_labels(
    template_id: int, item_ids: list[int], output_id: int, plugin_slug: str, **kwargs
):
    """Print multiple labels against the provided template.

    Arguments:
        template_id: The ID of the LabelTemplate to use
        item_ids: List of item IDs to generate the labels against
        output_id: The ID of the LabelOutput to use (if provided)
        plugin_slug: The ID of the LabelPlugin to use (if provided)

    This function is intended to be called by the background worker,
    and will continuously update the status of the LabelOutput object.
    """
    from plugin.registry import registry
    from report.models import LabelOutput, LabelTemplate

    try:
        template = LabelTemplate.objects.get(pk=template_id)
        output = LabelOutput.objects.get(pk=output_id)
    except Exception:
        log_error('report.tasks.print_labels')
        return

    # Fetch the items to be included in the report
    model = template.get_model()
    items = model.objects.filter(pk__in=item_ids)

    plugin = registry.get_plugin(plugin_slug)

    if not plugin:
        logger.warning("Label printing plugin '%s' not found", plugin_slug)
        return

    # Extract optional arguments for label printing
    options = kwargs.pop('options') or {}

    template.print(items, plugin, output=output, options=options)
