"""Tests for tasks in app common."""

from django.test import TestCase

from common.models import NotificationEntry
from InvenTree.tasks import offload_task

from . import tasks as common_tasks


class TaskTest(TestCase):
    """Tests for common tasks."""

    def test_delete(self):
        """Test that the task `delete_old_notifications` runs through without errors."""
        # check empty run
        self.assertEqual(NotificationEntry.objects.all().count(), 0)
        offload_task(common_tasks.delete_old_notifications,)
