"""Unit tests for task management."""

import os
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import transaction
from django.db.utils import NotSupportedError
from django.test import TestCase
from django.utils import timezone

import requests_mock
from django_q.models import OrmQ, Schedule, Task
from error_report.models import Error

import InvenTree.tasks
from common.models import InvenTreeSetting, InvenTreeUserSetting
from InvenTree.unit_test import PluginRegistryMixin

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


class InvenTreeTaskTests(PluginRegistryMixin, TestCase):
    """Unit tests for tasks."""

    def test_offloading(self):
        """Test task offloading."""
        # Run with function ref
        InvenTree.tasks.offload_task(get_result)

        # Run with string ref
        InvenTree.tasks.offload_task('InvenTree.test_tasks.get_result')

        # The error-path tests below all use force_sync=True so that the sync
        # resolution code is exercised regardless of whether background workers
        # happen to be running in this environment.

        # Malformed taskname
        with self.assertWarnsMessage(
            UserWarning, "WARNING: 'InvenTree' not started - Malformed function path"
        ):
            InvenTree.tasks.offload_task('InvenTree', force_sync=True)

        # Non existent app
        with self.assertWarnsMessage(
            UserWarning,
            "WARNING: 'InvenTreeABC.test_tasks.doesnotmatter' not started - No module named 'InvenTreeABC.test_tasks'",
        ):
            InvenTree.tasks.offload_task(
                'InvenTreeABC.test_tasks.doesnotmatter', force_sync=True
            )

        # Non existent function
        with self.assertWarnsMessage(
            UserWarning,
            "WARNING: 'InvenTree.test_tasks.doesnotexist' not started - No function named 'doesnotexist'",
        ):
            InvenTree.tasks.offload_task(
                'InvenTree.test_tasks.doesnotexist', force_sync=True
            )

    def test_offloading_deep_path(self):
        """Test that task paths with more than 3 components are resolved correctly.

        Previously the sync fallback split on '.' requiring exactly 3 parts,
        so a 4-part path raised ValueError and returned False with no warning.
        Now rsplit('.', 1) is used, so any depth works.
        """
        # 4-part valid path: module = 'InvenTree.test_helpers.sample_tasks', func = 'get_result'
        InvenTree.tasks.offload_task(
            'InvenTree.test_helpers.sample_tasks.get_result', force_sync=True
        )

        # 4-part path with a non-existent module — should warn cleanly rather than crash
        with self.assertWarnsMessage(
            UserWarning,
            "WARNING: 'InvenTreeABC.sub.tasks.doesnotmatter' not started - No module named 'InvenTreeABC.sub.tasks'",
        ):
            InvenTree.tasks.offload_task(
                'InvenTreeABC.sub.tasks.doesnotmatter', force_sync=True
            )

    def test_offloading_no_eval_bypass(self):
        """Verify that names in tasks.py scope cannot be resolved via an eval bypass.

        The previous implementation fell back to eval(func) when getattr returned
        None, evaluating the function name in the local scope of offload_task rather
        than in the target module. This meant a Python builtin like 'eval', or any
        name imported into tasks.py, could be invoked via a crafted taskname. The
        replacement uses only getattr on the imported module and rejects anything
        not found there.
        """
        # 'eval' is a Python builtin; it is not an attribute of InvenTree.test_tasks.
        # Previously eval('eval') in tasks.py's scope would resolve it; now it fails.
        with self.assertWarnsMessage(
            UserWarning,
            "WARNING: 'InvenTree.test_tasks.eval' not started - No function named 'eval'",
        ):
            InvenTree.tasks.offload_task('InvenTree.test_tasks.eval', force_sync=True)

    def test_task_heartbeat(self):
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

    @requests_mock.Mocker()
    def test_task_check_for_updates(self, requests_mocker):
        """Test update notification creation and deduplication."""
        from common.models import NotificationEntry, NotificationMessage
        from common.serializers import NotificationMessageSerializer

        self.ensurePluginsLoaded(force=True)

        user = User.objects.create_superuser(
            username='update_admin',
            email='update@example.com',
            password='test-password',
        )

        release_url = 'https://github.com/InvenTree/InvenTree/releases/tag/99.99.99'

        requests_mocker.get(
            'https://api.github.com/repos/inventree/inventree/releases/latest',
            json={'tag_name': '99.99.99', 'html_url': release_url},
        )

        InvenTreeSetting.set_setting('_INVENTREE_LATEST_VERSION', '')

        with (
            patch(
                'InvenTree.tasks.isInvenTreeUpToDate', return_value=False
            ) as mock_up_to_date,
            patch('InvenTree.tasks.check_daily_holdoff', return_value=True),
        ):
            InvenTree.tasks.check_for_updates()

            self.assertEqual(
                InvenTreeSetting.get_setting('_INVENTREE_LATEST_VERSION'), '99.99.99'
            )
            self.assertEqual(NotificationMessage.objects.count(), 1)
            self.assertEqual(NotificationEntry.objects.count(), 1)

            message = NotificationMessage.objects.get(user=user)
            entry = NotificationEntry.objects.get()

            self.assertEqual(message.link, release_url)
            self.assertEqual(entry.uid, 0)

            serialized = NotificationMessageSerializer(message).data
            self.assertEqual(serialized['target']['link'], release_url)

            InvenTree.tasks.check_for_updates()

            self.assertEqual(NotificationMessage.objects.count(), 1)
            self.assertEqual(NotificationEntry.objects.count(), 1)
            mock_up_to_date.assert_called()

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
        user = User.objects.create_user(
            username='i_am_staff', password='staffpass', is_staff=False, is_active=True
        )

        n_tasks = Task.objects.count()
        n_entries = NotificationEntry.objects.count()
        n_messages = NotificationMessage.objects.count()

        test_data = {
            'name': 'failed_task',
            'func': 'InvenTree.tasks.failed_task',
            'group': 'test',
            'success': False,
            'started': timezone.now(),
            'stopped': timezone.now(),
            'attempt_count': 10,
        }

        # Create a 'failed' task in the database
        # Note: The 'attempt count' is set to 10 to ensure that the task is properly marked as 'failed'
        Task.objects.create(id=n_tasks + 1, **test_data)

        # A new notification entry should NOT be created (yet) - due to lack of permission for the user
        self.assertEqual(NotificationEntry.objects.count(), n_entries + 0)
        self.assertEqual(NotificationMessage.objects.count(), n_messages + 0)

        # Give them all the required staff level permissions
        user.is_staff = True
        user.save()

        # Ensure error notifications are enabled for this user
        InvenTreeUserSetting.set_setting('NOTIFICATION_ERROR_REPORT', True, user=user)

        # Create a 'failed' task in the database
        # Note: The 'attempt count' is set to 10 to ensure that the task is properly marked as 'failed'
        Task.objects.create(id=n_tasks + 2, **test_data)

        # A new notification entry should be created (as the user now has permission to see it)
        self.assertEqual(NotificationEntry.objects.count(), n_entries + 1)
        self.assertEqual(NotificationMessage.objects.count(), n_messages + 1)

        msg = NotificationMessage.objects.last()

        self.assertEqual(msg.name, 'Server Error')
        self.assertEqual(msg.message, 'An error has been logged by the server.')

    def test_delete_old_emails(self):
        """Test the delete_old_emails task."""
        from common.models import EmailMessage

        # Create an email message
        self.create_mails()

        # Run the task
        InvenTreeSetting.set_setting('INVENTREE_DELETE_EMAIL_DAYS', 31)
        InvenTree.tasks.offload_task(InvenTree.tasks.delete_old_emails, force_sync=True)

        # Check that the email message has been deleted
        emails = EmailMessage.objects.all()
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0].subject, 'Test Email 2')

        # Set the setting higher than the threshold
        InvenTreeSetting.set_setting('INVENTREE_DELETE_EMAIL_DAYS', 30)

        # Run the task again
        InvenTree.tasks.offload_task(InvenTree.tasks.delete_old_emails, force_sync=True)
        emails = EmailMessage.objects.all()
        self.assertEqual(len(emails), 0)

        # Re-Add messages and enable a proper log
        self.create_mails()

        # Set the setting lower than the threshold
        InvenTreeSetting.set_setting('INVENTREE_DELETE_EMAIL_DAYS', 7)
        InvenTreeSetting.set_setting('INVENTREE_PROTECT_EMAIL_LOG', True)

        # Run the task again
        InvenTree.tasks.offload_task(InvenTree.tasks.delete_old_emails, force_sync=True)

        # Check that the email message has not been deleted
        emails = EmailMessage.objects.all()
        self.assertEqual(len(emails), 2)

    def create_mails(self):
        """Create some email messages for testing."""
        from common.models import EmailMessage

        start_mails = [
            ['Test Email 1', 'This is a test email.', 'abc@example.org', threshold_low],
            [
                'Test Email 2',
                'This is another test email.',
                'def@example.org',
                threshold,
            ],
        ]
        for subject, body, to, timestamp in start_mails:
            msg = EmailMessage.objects.create(
                subject=subject, body=body, to=to, priority=1
            )
            msg.timestamp = timestamp
            msg.save()

    def test_duplicate_tasks(self):
        """Test for task duplication."""
        # Start with a blank slate
        OrmQ.objects.all().delete()

        # Add some unique tasks
        for idx in range(10):
            InvenTree.tasks.offload_task(
                f'dummy_module.dummy_function_{idx}', force_async=True
            )

        self.assertEqual(OrmQ.objects.count(), 10)

        # Add some duplicate tasks
        for _idx in range(10):
            InvenTree.tasks.offload_task(
                'dummy_module.dummy_function_x',
                1,
                2,
                3,
                animal='cat',
                vegetable='carrot',
                force_async=True,
            )

        # Only 1 extra task should have been added
        self.assertEqual(OrmQ.objects.count(), 11)

        # Add some more duplicate tasks, but ignore duplication checks
        for _idx in range(10):
            InvenTree.tasks.offload_task(
                'dummy_module.dummy_function_y',
                1,
                2,
                3,
                animal='dog',
                vegetable='yam',
                force_async=True,
                check_duplicates=False,
            )

        # 10 extra tasks should have been added
        self.assertEqual(OrmQ.objects.count(), 21)

        # Add more tasks, which are *not* duplicates based on args
        for idx in range(10):
            InvenTree.tasks.offload_task(
                'dummy_module.dummy_function',
                1,
                idx,
                3,
                animal='cat',
                vegetable='carrot',
                force_async=True,
            )

        # Add more tasks, which are *not* duplicates based on kwargs
        for idx in range(10):
            InvenTree.tasks.offload_task(
                'dummy_module.dummy_function',
                1,
                2,
                3,
                animal='cat',
                vegetable=f'vegetable_{idx}',
                force_async=True,
            )

        # 20 more tasks should have been added
        self.assertEqual(OrmQ.objects.count(), 41)

    def test_bulk_offload(self):
        """Test the bulk_offload_task function."""
        # Start with a blank slate
        OrmQ.objects.all().delete()

        entries = [
            ((idx, idx + 1), {'animal': f'animal_{idx}', 'count': idx})
            for idx in range(10)
        ]

        # Queuing all 10 tasks should only take a single database write (bulk_create)
        with self.assertNumQueries(1):
            result = InvenTree.tasks.bulk_offload_task(
                'dummy_module.dummy_function', entries, force_async=True
            )

        self.assertTrue(result)
        self.assertEqual(OrmQ.objects.count(), 10)

        # Read out the pending tasks, and check that the args / kwargs match
        queued_tasks = OrmQ.objects.all().order_by('id')

        for task, (args, kwargs) in zip(queued_tasks, entries, strict=True):
            self.assertEqual(task.func(), 'dummy_module.dummy_function')
            self.assertEqual(task.group(), 'inventree')
            self.assertEqual(task.args(), args)
            self.assertEqual(task.kwargs(), kwargs)


class TaskBatchTests(TestCase):
    """Unit tests for the batch_offload_tasks() context manager."""

    def setUp(self):
        """Start each test with an empty task queue."""
        super().setUp()
        OrmQ.objects.all().delete()

    def test_tasks_queued_and_flushed_on_commit(self):
        """Tasks offloaded inside batch_offload_tasks() are queued and flushed as one bulk write on commit."""
        with self.captureOnCommitCallbacks(execute=True):
            with transaction.atomic(), InvenTree.tasks.batch_offload_tasks():
                for idx in range(10):
                    InvenTree.tasks.offload_task(
                        'dummy_module.dummy_function',
                        idx,
                        force_async=True,
                        animal=f'animal_{idx}',
                    )

                # Nothing should be queued yet - the batch only flushes on commit
                self.assertEqual(OrmQ.objects.count(), 0)

        self.assertEqual(OrmQ.objects.count(), 10)

        queued_tasks = OrmQ.objects.all().order_by('id')

        for idx, task in enumerate(queued_tasks):
            self.assertEqual(task.func(), 'dummy_module.dummy_function')
            self.assertEqual(task.group(), 'inventree')
            self.assertEqual(task.args(), (idx,))
            self.assertEqual(task.kwargs(), {'animal': f'animal_{idx}'})

    def test_tasks_grouped_by_name_and_group(self):
        """Tasks with different (taskname, group) combinations are flushed as separate bulk writes."""
        with self.captureOnCommitCallbacks(execute=True):
            with transaction.atomic(), InvenTree.tasks.batch_offload_tasks():
                for idx in range(5):
                    InvenTree.tasks.offload_task(
                        'dummy_module.task_a', idx, force_async=True, group='alpha'
                    )
                for idx in range(3):
                    InvenTree.tasks.offload_task(
                        'dummy_module.task_b', idx, force_async=True, group='beta'
                    )

        self.assertEqual(OrmQ.objects.count(), 8)
        self.assertEqual(
            sum(
                1
                for t in OrmQ.objects.all()
                if t.func() == 'dummy_module.task_a' and t.group() == 'alpha'
            ),
            5,
        )
        self.assertEqual(
            sum(
                1
                for t in OrmQ.objects.all()
                if t.func() == 'dummy_module.task_b' and t.group() == 'beta'
            ),
            3,
        )

    def test_tasks_discarded_on_rollback(self):
        """Tasks queued in a batch are discarded, not fired, if the transaction rolls back."""
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic(), InvenTree.tasks.batch_offload_tasks():
                    InvenTree.tasks.offload_task(
                        'dummy_module.dummy_function', force_async=True
                    )
                    raise ValueError('boom')
            except ValueError:
                pass

        self.assertEqual(OrmQ.objects.count(), 0)

    def test_tasks_outside_batch_fire_immediately(self):
        """Tasks offloaded outside any batch_offload_tasks() context are unaffected - fired immediately."""
        InvenTree.tasks.offload_task('dummy_module.dummy_function', force_async=True)

        # No transaction commit or captureOnCommitCallbacks needed - it was never queued
        self.assertEqual(OrmQ.objects.count(), 1)

    def test_nested_batch_share_one_flush(self):
        """A nested batch_offload_tasks() call reuses the outer batch, rather than flushing twice."""
        with self.captureOnCommitCallbacks(execute=True):
            with transaction.atomic(), InvenTree.tasks.batch_offload_tasks():
                InvenTree.tasks.offload_task(
                    'dummy_module.dummy_function', 1, force_async=True
                )
                with InvenTree.tasks.batch_offload_tasks():
                    InvenTree.tasks.offload_task(
                        'dummy_module.dummy_function', 2, force_async=True
                    )
                self.assertEqual(OrmQ.objects.count(), 0)

        self.assertEqual(OrmQ.objects.count(), 2)

    def test_force_sync_excluded_from_batch(self):
        """force_sync=True calls bypass batch_offload_tasks() entirely and run immediately."""
        calls = []

        def sync_target():
            calls.append('ran')

        with self.captureOnCommitCallbacks(execute=True):
            with transaction.atomic(), InvenTree.tasks.batch_offload_tasks():
                InvenTree.tasks.offload_task(sync_target, force_sync=True)

                # Ran immediately - not deferred to flush, and never touched the task queue
                self.assertEqual(calls, ['ran'])
                self.assertEqual(OrmQ.objects.count(), 0)

                InvenTree.tasks.offload_task(
                    'dummy_module.dummy_function', force_async=True
                )

                # The (non-force_sync) async call is queued, not yet in OrmQ
                self.assertEqual(OrmQ.objects.count(), 0)

        # After commit: only the batched async call produced an OrmQ entry
        self.assertEqual(OrmQ.objects.count(), 1)
        self.assertEqual(calls, ['ran'])

    def test_batched_calls_skip_duplicate_check(self):
        """Unlike individual offload_task() calls, batched calls are never deduplicated."""
        with self.captureOnCommitCallbacks(execute=True):
            with transaction.atomic(), InvenTree.tasks.batch_offload_tasks():
                for _ in range(3):
                    InvenTree.tasks.offload_task(
                        'dummy_module.dummy_function_dup',
                        1,
                        2,
                        animal='cat',
                        force_async=True,
                    )

        # All 3 identical calls were queued, unlike the non-batched dedup behavior
        # exercised in InvenTreeTaskTests.test_duplicate_tasks
        self.assertEqual(OrmQ.objects.count(), 3)
