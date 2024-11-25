"""Unit tests for task management."""

import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db.utils import NotSupportedError
from django.test import TestCase
from django.utils import timezone

from django_q.models import Schedule, Task
from error_report.models import Error

import InvenTree.tasks
from common.models import InvenTreeSetting

threshold = timezone.now() - timedelta(days=30)
threshold_low = threshold - timedelta(days=1)


class ScheduledTaskTests(TestCase):
    """Unit tests for scheduled tasks."""

    def get_tasks(self, name):
        """Helper function to get a Schedule object."""
        return Schedule.objects.filter(func=name)

    def test_add_task(self):
        """Ensure that duplicate tasks cannot be added."""
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


def get_result():
    """Demo function for test_offloading."""
    return 'abc'


class InvenTreeTaskTests(TestCase):
    """Unit tests for tasks."""

    def test_offloading(self):
        """Test task offloading."""
        # Run with function ref
        InvenTree.tasks.offload_task(get_result)

        # Run with string ref
        InvenTree.tasks.offload_task('InvenTree.test_tasks.get_result')

        # Error runs
        # Malformed taskname
        with self.assertWarnsMessage(
            UserWarning, "WARNING: 'InvenTree' not started - Malformed function path"
        ):
            InvenTree.tasks.offload_task('InvenTree')

        # Non existent app
        with self.assertWarnsMessage(
            UserWarning,
            "WARNING: 'InvenTreeABC.test_tasks.doesnotmatter' not started - No module named 'InvenTreeABC.test_tasks'",
        ):
            InvenTree.tasks.offload_task('InvenTreeABC.test_tasks.doesnotmatter')

        # Non existent function
        with self.assertWarnsMessage(
            UserWarning,
            "WARNING: 'InvenTree.test_tasks.doesnotexist' not started - No function named 'doesnotexist'",
        ):
            InvenTree.tasks.offload_task('InvenTree.test_tasks.doesnotexist')

    def test_task_hearbeat(self):
        """Test the task heartbeat."""
        InvenTree.tasks.offload_task(InvenTree.tasks.heartbeat)

    def test_task_delete_successful_tasks(self):
        """Test the task delete_successful_tasks."""
        from django_q.models import Success

        Success.objects.create(
            name='abc', func='abc', stopped=threshold, started=threshold_low
        )
        InvenTree.tasks.offload_task(InvenTree.tasks.delete_successful_tasks)
        results = Success.objects.filter(started__lte=threshold)
        self.assertEqual(len(results), 0)

    def test_task_delete_old_error_logs(self):
        """Test the task delete_old_error_logs."""
        # Create error
        error_obj = Error.objects.create()
        error_obj.when = threshold_low
        error_obj.save()

        # Check that it is not empty
        errors = Error.objects.filter(when__lte=threshold)
        self.assertNotEqual(len(errors), 0)

        # Run action
        InvenTree.tasks.offload_task(InvenTree.tasks.delete_old_error_logs)

        # Check that it is empty again
        errors = Error.objects.filter(when__lte=threshold)
        self.assertEqual(len(errors), 0)

    def test_task_check_for_updates(self):
        """Test the task check_for_updates."""
        # Check that setting should be empty
        InvenTreeSetting.set_setting('_INVENTREE_LATEST_VERSION', '')
        self.assertEqual(InvenTreeSetting.get_setting('_INVENTREE_LATEST_VERSION'), '')

        # Get new version
        InvenTree.tasks.offload_task(InvenTree.tasks.check_for_updates)

        # Check that setting is not empty
        response = InvenTreeSetting.get_setting('_INVENTREE_LATEST_VERSION')
        self.assertNotEqual(response, '')
        self.assertTrue(bool(response))

    def test_task_check_for_migrations(self):
        """Test the task check_for_migrations."""
        # Update disabled
        InvenTree.tasks.check_for_migrations()

        # Update enabled - no migrations
        os.environ['INVENTREE_AUTO_UPDATE'] = 'True'
        InvenTree.tasks.check_for_migrations()

        # List all current migrations for the InvenTree app
        migration_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'migrations'
        )

        migration_files = os.listdir(migration_dir)

        # Create migration
        self.assertEqual(len(InvenTree.tasks.get_migration_plan()), 0)
        call_command('makemigrations', ['InvenTree', '--empty'], interactive=False)
        self.assertEqual(len(InvenTree.tasks.get_migration_plan()), 1)

        # Run with migrations - catch no foreigner error
        try:
            InvenTree.tasks.check_for_migrations()
        except NotSupportedError as e:  # pragma: no cover
            if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
                raise e

        # Cleanup
        try:
            migration_name = InvenTree.tasks.get_migration_plan()[0][0].name + '.py'
            migration_path = (
                settings.BASE_DIR / 'InvenTree' / 'migrations' / migration_name
            )
            migration_path.unlink()
        except IndexError:  # pragma: no cover
            pass

        # Let's remove the newly created migration file
        for fn in os.listdir(migration_dir):
            fn = os.path.join(migration_dir, fn)

            if (
                os.path.isfile(fn)
                and fn not in migration_files
                and 'auto' in fn
                and fn.endswith('.py')
            ):
                print('Removing dummy migration file:', fn)
                os.remove(fn)

    def test_failed_task_notification(self):
        """Test that a failed task will generate a notification."""
        from common.models import NotificationEntry, NotificationMessage

        # Create a staff user (to ensure notifications are sent)
        User.objects.create_user(username='staff', password='staffpass', is_staff=True)

        n_tasks = Task.objects.count()
        n_entries = NotificationEntry.objects.count()
        n_messages = NotificationMessage.objects.count()

        # Create a 'failed' task in the database
        # Note: The 'attempt count' is set to 10 to ensure that the task is properly marked as 'failed'
        Task.objects.create(
            id=n_tasks + 1,
            name='failed_task',
            func='InvenTree.tasks.failed_task',
            group='test',
            success=False,
            started=timezone.now(),
            stopped=timezone.now(),
            attempt_count=10,
        )

        # A new notification entry should be created
        self.assertEqual(NotificationEntry.objects.count(), n_entries + 1)
        self.assertEqual(NotificationMessage.objects.count(), n_messages + 1)

        msg = NotificationMessage.objects.last()

        self.assertEqual(msg.name, 'Task Failure')
        self.assertEqual(
            msg.message,
            "Background worker task 'InvenTree.tasks.failed_task' failed after 10 attempts",
        )
