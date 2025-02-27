"""Background tasks for the report app."""

from datetime import timedelta

from InvenTree.exceptions import log_error
from InvenTree.helpers import current_time
from InvenTree.tasks import ScheduledTask, scheduled_task
from report.models import LabelOutput, ReportOutput


@scheduled_task(ScheduledTask.DAILY)
def cleanup_old_report_outputs():
    """Remove old report/label outputs from the database."""
    # Remove any outputs which are older than 5 days
    threshold = current_time() - timedelta(days=5)

    LabelOutput.objects.filter(created__lte=threshold).delete()
    ReportOutput.objects.filter(created__lte=threshold).delete()


def print_report(template_id: int, item_ids: list[int], output_id: int, **kwargs):
    """Print a report against the provided template.

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
    except Exception:
        log_error('report.tasks.print_report')
        return

    # Fetch the output object to print against
    output = ReportOutput.objects.get(pk=output_id)

    # Fetch the items to be included in the report
    model = template.get_model()
    items = model.objects.filter(pk__in=item_ids)

    template.print(items, output=output)
