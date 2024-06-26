"""Background tasks for the report app."""

from datetime import timedelta

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
