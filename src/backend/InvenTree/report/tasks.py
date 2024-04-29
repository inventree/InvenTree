"""Background tasks for the report app."""

from datetime import timedelta

from InvenTree.helpers import current_time
from InvenTree.tasks import ScheduledTask, scheduled_task
from report.models import TemplateOutput


@scheduled_task(ScheduledTask.DAILY)
def cleanup_old_report_outputs():
    """Remove old report/label outputs from the database."""
    # Remove any outputs which are older than 5 days
    TemplateOutput.objects.filter(
        created__lte=current_time() - timedelta(days=5)
    ).delete()
