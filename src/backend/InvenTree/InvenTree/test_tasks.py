"""Unit tests for task management."""

import logging
import os
import queue
import time
from datetime import timedelta
from multiprocessing import Value
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


retry_regression_logger = logging.getLogger('InvenTree.test_tasks.retry_regression')

RETRY_REGRESSION_LOG_MESSAGE = 'retry regression task executed'


def always_fails_task():
    """Demo function for the worker retry regression tests below.

    Logs a fixed, greppable message and then always raises - so a test can count exactly
    how many times a real django-q2 worker actually invoked it.
    """
    retry_regression_logger.info(RETRY_REGRESSION_LOG_MESSAGE)
    raise ValueError('always_fails_task: intentional failure for retry regression test')


TIMEOUT_TASK_SLEEP_SECONDS = 5
TIMEOUT_TASK_STARTED_LOG_MESSAGE = 'timeout regression task started'
TIMEOUT_TASK_FINISHED_LOG_MESSAGE = 'timeout regression task finished sleeping'


def slow_task_for_timeout_test():
    """Demo function for the timeout regression test below.

    Sleeps far longer than the per-task timeout under test. If a real timeout does not
    interrupt it, FINISHED gets logged - so that message must never appear.
    """
    retry_regression_logger.info(TIMEOUT_TASK_STARTED_LOG_MESSAGE)
    time.sleep(TIMEOUT_TASK_SLEEP_SECONDS)
    retry_regression_logger.info(TIMEOUT_TASK_FINISHED_LOG_MESSAGE)


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

    def test_offload_no_retry(self):
        """retry=False should mark the queued task with ack_failure=True.

        This is the bandaid for django-q2 having no per-task retry limit: 'ack_failure'
        is its native per-task option that drops a task the moment it fails, instead of
        leaving it to be redelivered indefinitely by the ORM broker.
        """
        OrmQ.objects.all().delete()

        InvenTree.tasks.offload_task(
            'dummy_module.dummy_function', force_async=True, retry=False
        )

        task = OrmQ.objects.get()
        self.assertTrue(task.q_options().get('ack_failure'))

        # By default (retry=True), the task is not marked for single-shot execution
        OrmQ.objects.all().delete()
        InvenTree.tasks.offload_task('dummy_module.dummy_function', force_async=True)
        task = OrmQ.objects.get()
        self.assertFalse(task.q_options().get('ack_failure'))

    def test_offload_timeout(self):
        """timeout=N must actually be enforced by the worker, not just recorded on the queue.

        django-q2 supports 'timeout' as a native per-task option.
        This offloads a task that sleeps far longer than the timeout,
        and drives it through the real worker() pipeline,
        to prove it gets killed at the timeout rather than left to run.
        """
        from django_q.brokers import get_broker

        OrmQ.objects.all().delete()

        InvenTree.tasks.offload_task(
            'InvenTree.test_tasks.slow_task_for_timeout_test',
            force_async=True,
            timeout=1,
        )

        # The per-task override must have been recorded on the queued task
        queued = OrmQ.objects.get()
        self.assertEqual(queued.q_options().get('timeout'), 1)

        # Without an explicit timeout, no per-task override is set - the cluster-wide
        # default applies
        OrmQ.objects.all().delete()
        InvenTree.tasks.offload_task('dummy_module.dummy_function', force_async=True)
        queued = OrmQ.objects.get()
        self.assertNotIn('timeout', queued.q_options())

        # Now offload the slow task for real, and drive it through the actual worker
        OrmQ.objects.all().delete()
        InvenTree.tasks.offload_task(
            'InvenTree.test_tasks.slow_task_for_timeout_test',
            force_async=True,
            timeout=1,
        )

        broker = get_broker()

        start = time.monotonic()
        with self.assertLogs(retry_regression_logger, level='INFO') as captured:
            executed = self.run_one_broker_cycle(broker)
        elapsed = time.monotonic() - start

        self.assertEqual(executed, 1)

        # The task must have started, but the 1-second timeout must have killed it well
        # before its 5-second sleep completes - it never gets to log that it finished
        self.assertTrue(
            any(TIMEOUT_TASK_STARTED_LOG_MESSAGE in line for line in captured.output)
        )
        self.assertFalse(
            any(TIMEOUT_TASK_FINISHED_LOG_MESSAGE in line for line in captured.output)
        )
        self.assertLess(elapsed, TIMEOUT_TASK_SLEEP_SECONDS)

        # The task must be recorded as failed, specifically due to the timeout
        saved_task = Task.objects.get(
            func='InvenTree.test_tasks.slow_task_for_timeout_test'
        )
        self.assertFalse(saved_task.success)
        self.assertIn('exceeded maximum timeout value', saved_task.result)

    def test_bulk_offload_timeout(self):
        """bulk_offload_task() should forward timeout=N to every queued task."""
        OrmQ.objects.all().delete()

        entries = [((idx,), {}) for idx in range(5)]

        InvenTree.tasks.bulk_offload_task(
            'dummy_module.dummy_function', entries, force_async=True, timeout=15
        )

        self.assertEqual(OrmQ.objects.count(), 5)
        for task in OrmQ.objects.all():
            self.assertEqual(task.q_options().get('timeout'), 15)

    def test_offload_timeout_validation(self):
        """A per-task timeout must be clamped to leave headroom before the broker's redelivery interval.

        The broker redelivers a task once its lock (governed by the cluster-wide
        Q_CLUSTER['retry'] setting) expires, regardless of any per-task 'timeout'
        override. If 'timeout' left less than 120s of headroom before that, the task
        could be redelivered and executed again before the original attempt had even
        timed out - so offload_task()/bulk_offload_task() must clamp it down (and warn)
        rather than queuing it as requested.
        """
        retry = settings.Q_CLUSTER['retry']
        max_timeout = retry - 120

        # A timeout comfortably below the retry interval is left untouched
        OrmQ.objects.all().delete()
        InvenTree.tasks.offload_task(
            'dummy_module.dummy_function', force_async=True, timeout=retry - 200
        )
        task = OrmQ.objects.get()
        self.assertEqual(task.q_options().get('timeout'), retry - 200)

        # A timeout equal to the retry interval leaves no headroom at all - clamped
        # down to the maximum safe value, with a warning logged
        OrmQ.objects.all().delete()
        with self.assertLogs('inventree', level='WARNING') as captured:
            InvenTree.tasks.offload_task(
                'dummy_module.dummy_function', force_async=True, timeout=retry
            )
        self.assertTrue(any('clamping' in line for line in captured.output))
        task = OrmQ.objects.get()
        self.assertEqual(task.q_options().get('timeout'), max_timeout)

        # Also enforced directly by bulk_offload_task()
        OrmQ.objects.all().delete()
        with self.assertLogs('inventree', level='WARNING') as captured:
            InvenTree.tasks.bulk_offload_task(
                'dummy_module.dummy_function',
                [((), {})],
                force_async=True,
                timeout=retry,
            )
        self.assertTrue(any('clamping' in line for line in captured.output))
        task = OrmQ.objects.get()
        self.assertEqual(task.q_options().get('timeout'), max_timeout)

    def test_duplicate_check_respects_retry_and_timeout(self):
        """check_existing_task() must not treat different retry/timeout policies as duplicates.

        Regression test: previously, queuing the same (taskname, group, args, kwargs)
        with a different 'retry' or 'timeout' would be silently swallowed as a
        'duplicate' of whatever was already queued, discarding the newly requested
        policy entirely.
        """
        OrmQ.objects.all().delete()

        first_id = InvenTree.tasks.offload_task(
            'dummy_module.dummy_function', force_async=True
        )

        # Same call, but requesting retry=False - must not be treated as a duplicate
        second_id = InvenTree.tasks.offload_task(
            'dummy_module.dummy_function', force_async=True, retry=False
        )
        self.assertNotEqual(first_id, second_id)
        self.assertEqual(OrmQ.objects.count(), 2)

        # Same call again, but with a different timeout - also not a duplicate
        third_id = InvenTree.tasks.offload_task(
            'dummy_module.dummy_function', force_async=True, retry=False, timeout=30
        )
        self.assertNotEqual(third_id, second_id)
        self.assertEqual(OrmQ.objects.count(), 3)

        # Only an exact match of retry AND timeout is deduplicated
        fourth_id = InvenTree.tasks.offload_task(
            'dummy_module.dummy_function', force_async=True, retry=False, timeout=30
        )
        self.assertEqual(fourth_id, third_id)
        self.assertEqual(OrmQ.objects.count(), 3)

    def run_one_broker_cycle(self, broker):
        """Drive a single dequeue/execute/save-or-acknowledge pass through django-q2.

        Uses the actual pusher/worker/monitor functions - exactly what a real qcluster
        worker process does, just without the multiprocessing.

        Returns the number of tasks that were dequeued and executed in this pass.
        """
        from django_q.monitor import monitor
        from django_q.signing import SignedPackage
        from django_q.worker import worker

        dequeued = broker.dequeue()
        if not dequeued:
            return 0

        task_queue = queue.Queue()
        result_queue = queue.Queue()

        for ack_id, payload in dequeued:
            task = SignedPackage.loads(payload)
            task['ack_id'] = ack_id
            task_queue.put(task)
        task_queue.put('STOP')

        # worker()/monitor() normally run in their own dedicated process, so closing
        # 'old' django database connections there is harmless. Here they run inline on
        # the test's own connection (wrapped in TestCase's atomic transaction), so that
        # same call would tear down the connection this test needs afterwards.
        with (
            patch('django_q.worker.close_old_django_connections'),
            patch('django_q.monitor.close_old_django_connections'),
        ):
            worker(task_queue, result_queue, Value('i', -1))

            result_queue.put('STOP')
            monitor(result_queue, broker)

        return len(dequeued)

    def test_worker_does_not_retry_when_retry_false(self):
        """Regression test: retry=False must stop a real worker from re-running a failing task.

        Rather than just inspecting the queued payload, this drives the task through
        django-q2's actual pusher/worker/monitor pipeline (the same functions a real
        qcluster worker uses) to prove the task is genuinely never re-executed.
        """
        from django_q.brokers import get_broker

        OrmQ.objects.all().delete()

        InvenTree.tasks.offload_task(
            'InvenTree.test_tasks.always_fails_task', force_async=True, retry=False
        )

        broker = get_broker()

        with self.assertLogs(retry_regression_logger, level='INFO') as captured:
            executed = self.run_one_broker_cycle(broker)

        self.assertEqual(executed, 1)
        self.assertEqual(
            sum(RETRY_REGRESSION_LOG_MESSAGE in line for line in captured.output), 1
        )

        # The failed task must have been dropped, not left queued for redelivery
        self.assertEqual(OrmQ.objects.count(), 0)

        # Even simulating the redelivery timeout having elapsed, there is nothing left
        # in the broker to redeliver - the task only ever ran once
        self.assertEqual(self.run_one_broker_cycle(broker), 0)

    def test_worker_retries_by_default(self):
        """Contrast case for test_worker_does_not_retry_when_retry_false().

        With the default retry=True, a failing task is left queued and gets picked up
        and re-executed again once the broker's redelivery timeout has elapsed.
        """
        from django_q.brokers import get_broker

        OrmQ.objects.all().delete()

        InvenTree.tasks.offload_task(
            'InvenTree.test_tasks.always_fails_task', force_async=True
        )

        broker = get_broker()

        with self.assertLogs(retry_regression_logger, level='INFO') as captured:
            executed = self.run_one_broker_cycle(broker)

        self.assertEqual(executed, 1)
        self.assertEqual(
            sum(RETRY_REGRESSION_LOG_MESSAGE in line for line in captured.output), 1
        )

        # The failed task must still be queued, waiting to be redelivered
        self.assertEqual(OrmQ.objects.count(), 1)

        # Simulate the redelivery timeout having elapsed, then let the worker pick the
        # same task up again
        OrmQ.objects.update(lock=timezone.now() - timedelta(seconds=1))

        with self.assertLogs(retry_regression_logger, level='INFO') as captured:
            executed = self.run_one_broker_cycle(broker)

        self.assertEqual(executed, 1)
        self.assertEqual(
            sum(RETRY_REGRESSION_LOG_MESSAGE in line for line in captured.output), 1
        )

    def test_single_shot_task_failure_notifies_immediately(self):
        """retry=False task failures must raise the 'Task Failure' notification on their one attempt.

        Regression test: after_failed_task() only notifies once a task's attempt_count
        reaches Q_CLUSTER['max_attempts'] (5 by default). A retry=False task is dropped
        by the broker after a single failed attempt (see test_worker_does_not_retry_when_retry_false),
        so attempt_count never reaches that threshold and the notification would
        otherwise never fire. InvenTree.models.after_single_shot_task_failure() (hooked
        into django-q2's post_execute signal) must notify immediately instead.
        """
        from django_q.brokers import get_broker

        OrmQ.objects.all().delete()
        Error.objects.all().delete()

        InvenTree.tasks.offload_task(
            'InvenTree.test_tasks.always_fails_task', force_async=True, retry=False
        )

        broker = get_broker()

        with self.assertLogs(retry_regression_logger, level='INFO'):
            self.run_one_broker_cycle(broker)

        self.assertTrue(Error.objects.filter(kind='Task Failure').exists())

    def test_retryable_task_failure_does_not_notify_early(self):
        """Contrast case for test_single_shot_task_failure_notifies_immediately().

        A single failed attempt of a retry=True task must NOT raise the 'Task Failure'
        notification - it is still eligible for redelivery, so the notification should
        only fire once Q_CLUSTER['max_attempts'] is actually reached (covered by the
        existing after_failed_task() post_save logic, not exercised by this test).
        """
        from django_q.brokers import get_broker

        OrmQ.objects.all().delete()
        Error.objects.all().delete()

        InvenTree.tasks.offload_task(
            'InvenTree.test_tasks.always_fails_task', force_async=True
        )

        broker = get_broker()

        with self.assertLogs(retry_regression_logger, level='INFO'):
            self.run_one_broker_cycle(broker)

        self.assertFalse(Error.objects.filter(kind='Task Failure').exists())

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
            self.assertEqual(entry.uid, '0')

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

    def test_bulk_offload_no_retry(self):
        """bulk_offload_task() should mark every queued task with ack_failure=True when retry=False."""
        OrmQ.objects.all().delete()

        entries = [((idx,), {}) for idx in range(5)]

        InvenTree.tasks.bulk_offload_task(
            'dummy_module.dummy_function', entries, force_async=True, retry=False
        )

        self.assertEqual(OrmQ.objects.count(), 5)
        for task in OrmQ.objects.all():
            self.assertTrue(task.q_options().get('ack_failure'))


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

    def test_tasks_grouped_by_retry(self):
        """Tasks with different retry values are flushed as separate bulk writes."""
        with self.captureOnCommitCallbacks(execute=True):
            with transaction.atomic(), InvenTree.tasks.batch_offload_tasks():
                InvenTree.tasks.offload_task(
                    'dummy_module.task_a', 1, force_async=True, retry=False
                )
                InvenTree.tasks.offload_task('dummy_module.task_a', 2, force_async=True)

        self.assertEqual(OrmQ.objects.count(), 2)

        ack_failure_by_arg = {
            task.args()[0]: bool(task.q_options().get('ack_failure'))
            for task in OrmQ.objects.all()
        }
        self.assertEqual(ack_failure_by_arg, {1: True, 2: False})

    def test_tasks_grouped_by_timeout(self):
        """Tasks with different timeout values are flushed as separate bulk writes."""
        with self.captureOnCommitCallbacks(execute=True):
            with transaction.atomic(), InvenTree.tasks.batch_offload_tasks():
                InvenTree.tasks.offload_task(
                    'dummy_module.task_a', 1, force_async=True, timeout=5
                )
                InvenTree.tasks.offload_task('dummy_module.task_a', 2, force_async=True)

        self.assertEqual(OrmQ.objects.count(), 2)

        timeout_by_arg = {
            task.args()[0]: task.q_options().get('timeout')
            for task in OrmQ.objects.all()
        }
        self.assertEqual(timeout_by_arg, {1: 5, 2: None})

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
