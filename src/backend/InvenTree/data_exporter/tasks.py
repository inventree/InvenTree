"""Background tasks for the exporting app."""

from datetime import timedelta

from data_exporter.models import ExportOutput
from InvenTree.helpers import current_time
from InvenTree.tasks import ScheduledTask, scheduled_task


@scheduled_task(ScheduledTask.DAILY)
def cleanup_old_export_outputs():
    """Remove old export outputs from the database."""
    # Remove any outputs which are older than 5 days
    threshold = current_time() - timedelta(days=5)

    ExportOutput.objects.filter(created__lte=threshold).delete()
