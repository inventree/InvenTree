"""
Unit tests for task management
"""

from django.test import TestCase
from django_q.models import Schedule

import InvenTree.tasks


class ScheduledTaskTests(TestCase):
    """
    Unit tests for scheduled tasks
    """

    def get_tasks(self, name):

        return Schedule.objects.filter(func=name)

    def test_add_task(self):
        """
        Ensure that duplicate tasks cannot be added.
        """

        task = 'InvenTree.tasks.heartbeat'

        self.assertEqual(self.get_tasks(task).count(), 0)

        InvenTree.tasks.schedule_task(task, schedule_type=Schedule.MINUTES, minutes=10)

        self.assertEqual(self.get_tasks(task).count(), 1)

        t = Schedule.objects.get(func=task)

        self.assertEqual(t.minutes, 10)

        # Attempt to schedule the same task again
        InvenTree.tasks.schedule_task(task, schedule_type=Schedule.MINUTES, minutes=5)
        self.assertEqual(self.get_tasks(task).count(), 1)

        # But the 'minutes' should have been updated
        t = Schedule.objects.get(func=task)
        self.assertEqual(t.minutes, 5)


class InvenTreeTaskTests(TestCase):
    """Unit tests for tasks"""

    def test_task_hearbeat(self):
        """Test the task heartbeat"""
        InvenTree.tasks.offload_task(InvenTree.tasks.heartbeat)

    def test_task_delete_successful_tasks(self):
        """Test the task delete_successful_tasks"""
        InvenTree.tasks.offload_task(InvenTree.tasks.delete_successful_tasks)

    def test_task_delete_old_error_logs(self):
        """Test the task delete_old_error_logs"""
        InvenTree.tasks.offload_task(InvenTree.tasks.delete_old_error_logs)

    def test_task_check_for_updates(self):
        """Test the task check_for_updates"""
        InvenTree.tasks.offload_task(InvenTree.tasks.check_for_updates)
