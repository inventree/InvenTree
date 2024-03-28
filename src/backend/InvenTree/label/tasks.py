"""Background tasks for the label app."""

from datetime import timedelta

from django.utils import timezone

from InvenTree.tasks import ScheduledTask, scheduled_task
from label.models import LabelOutput


@scheduled_task(ScheduledTask.DAILY)
def cleanup_old_label_outputs():
    """Remove old label outputs from the database."""
    # Remove any label outputs which are older than 30 days
    LabelOutput.objects.filter(created__lte=timezone.now() - timedelta(days=5)).delete()
