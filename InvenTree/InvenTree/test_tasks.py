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
