"""Unit tests for scheduled tasks."""

import threading
from unittest import mock

from django.db import connection
from django.db.models.query import QuerySet
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature

from plugin import InvenTreePlugin
from plugin.helpers import MixinImplementationError
from plugin.mixins import ScheduleMixin
from plugin.registry import call_plugin_function, registry


class ExampleScheduledTaskPluginTests(TestCase):
    """Tests for provided ScheduledTaskPlugin."""

    def test_function(self):
        """Check if the scheduling works."""
        # The plugin should be defined
        self.assertIn('schedule', registry.plugins)
        plg = registry.plugins['schedule']
        self.assertTrue(plg)

        # check that the built-in function is running
        self.assertEqual(plg.member_func(), False)

        # register
        plg.register_tasks()
        # check that schedule was registers
        from django_q.models import Schedule

        # check that the tasks are defined
        self.assertEqual(
            plg.get_task_names(),
            [
                'plugin.schedule.member',
                'plugin.schedule.hello',
                'plugin.schedule.world',
            ],
        )

        scheduled_plugin_tasks = Schedule.objects.filter(name__istartswith='plugin.')
        self.assertEqual(len(scheduled_plugin_tasks), 3)

        # test updating the schedule
        hello_schedule = Schedule.objects.get(name='plugin.schedule.hello')
        self.assertEqual(hello_schedule.minutes, 45)
        # change the schedule and reregister -> the interval should be preserved
        plg.scheduled_tasks['hello']['minutes'] = 15
        # add a doubly scheduled task - this should be removed
        Schedule.objects.create(name='plugin.schedule.hello')
        self.assertEqual(
            Schedule.objects.filter(name='plugin.schedule.hello').count(), 2
        )

        plg.register_tasks()
        # The duplicate task should be removed
        self.assertEqual(
            Schedule.objects.filter(name='plugin.schedule.hello').count(), 1
        )

        # Check that the schedule was updated
        hello_schedule = Schedule.objects.get(name='plugin.schedule.hello')
        scheduled_plugin_tasks = Schedule.objects.filter(name__istartswith='plugin.')
        self.assertEqual(hello_schedule.minutes, 15)
        self.assertEqual(len(scheduled_plugin_tasks), 3)

        # delete middle task
        # this is to check the system also deals with disappearing tasks
        scheduled_plugin_tasks[1].delete()
        # there should be one less now
        scheduled_plugin_tasks = Schedule.objects.filter(name__istartswith='plugin.')
        self.assertEqual(len(scheduled_plugin_tasks), 2)

        # test unregistering
        plg.unregister_tasks()
        scheduled_plugin_tasks = Schedule.objects.filter(name__istartswith='plugin.')
        self.assertEqual(len(scheduled_plugin_tasks), 0)

    def test_calling(self):
        """Test calling of plugin functions by name."""
        # First, plugin is *not* enabled
        registry.set_plugin_state('schedule', False)

        with self.assertRaises(AttributeError):
            self.assertEqual(call_plugin_function('schedule', 'member_func'), False)

        registry.set_plugin_state('schedule', True)

        # Should work now
        self.assertEqual(call_plugin_function('schedule', 'member_func'), False)

        # Check with wrong key
        with self.assertRaises(AttributeError):
            call_plugin_function('does_not_exist', 'member_func'), None


@skipUnlessDBFeature('has_select_for_update')
class ScheduleMixinConcurrencyTest(TransactionTestCase):
    """Genuine cross-transaction regression test for ScheduleMixin.register_tasks().

    django_q's Schedule.name has no DB-level unique constraint, so two concurrent activation passes (e.g. multiple
    worker processes starting up together) could both find zero matching Schedule
    rows for a task and both create one - leaving a duplicate scheduled task that
    then fires twice per interval.

    register_tasks() now locks the plugin's PluginConfig row (select_for_update)
    for the duration of task registration, so only one of two concurrent calls may
    proceed through the check-then-write at a time.

    This relies on genuine database-level row locking, which SQLite does not
    provide - select_for_update() is silently a no-op there (Django's sqlite
    backend reports has_select_for_update=False), so both threads can race
    through the check-then-write and a "database is locked" error from one
    thread can roll back an otherwise-successful transaction, making the test
    flaky under sqlite for reasons unrelated to the code under test. Only run
    it against backends where the lock is real (e.g. postgres, mysql).
    """

    def test_concurrent_register_tasks_does_not_duplicate(self):
        """Two concurrent register_tasks() calls for the same plugin must not create duplicate Schedule rows."""
        from django_q.models import Schedule

        plg = registry.plugins['schedule']
        self.assertTrue(plg)

        # Warm the plugin-config cache in the main thread first, so the race
        # window below only covers register_tasks() itself, not the (variable
        # latency) first-time cache population that plugin_config() may trigger
        self.assertIsNotNone(plg.plugin_config())

        # Start from a clean slate
        Schedule.objects.filter(name__istartswith='plugin.schedule.').delete()

        start_barrier = threading.Barrier(2, timeout=15)
        errors = []

        # Wrap select_for_update() so both threads reach the (real, database-level)
        # PluginConfig row lock at the same time - one wins the lock and proceeds
        # through its full check-then-write, the other blocks until the winner's
        # transaction completes.
        original_select_for_update = QuerySet.select_for_update

        def synced_select_for_update(self_qs, *args, **kwargs):
            start_barrier.wait(timeout=15)
            return original_select_for_update(self_qs, *args, **kwargs)

        def run():
            try:
                plg.register_tasks()
            except Exception as exc:  # pragma: no cover - surfaced via errors list
                errors.append(exc)
            finally:
                connection.close()

        thread_a = threading.Thread(target=run)
        thread_b = threading.Thread(target=run)

        with mock.patch.object(QuerySet, 'select_for_update', synced_select_for_update):
            thread_a.start()
            thread_b.start()
            thread_a.join(timeout=10)
            thread_b.join(timeout=10)

        self.assertEqual(errors, [])

        # Exactly one Schedule row per task, not two
        for task_name in plg.get_task_names():
            self.assertEqual(
                Schedule.objects.filter(name=task_name).count(),
                1,
                f'Duplicate Schedule row created for {task_name}',
            )


class ScheduledTaskPluginTests(TestCase):
    """Tests for ScheduledTaskPluginTests mixin base."""

    def test_init(self):
        """Check that all MixinImplementationErrors raise."""

        class Base(ScheduleMixin, InvenTreePlugin):
            NAME = 'APlugin'

        class NoSchedules(Base):
            """Plugin without schedules."""

        with self.assertRaises(MixinImplementationError):
            NoSchedules().register_tasks()

        class WrongFuncSchedules(Base):
            """Plugin with broken functions.

            This plugin is missing a func
            """

            SCHEDULED_TASKS = {'test': {'schedule': 'I', 'minutes': 30}}

            def test(self):
                pass  # pragma: no cover

        with self.assertRaises(MixinImplementationError):
            WrongFuncSchedules().register_tasks()

        class WrongFuncSchedules1(WrongFuncSchedules):
            """Plugin with broken functions.

            This plugin is missing a schedule
            """

            SCHEDULED_TASKS = {'test': {'func': 'test', 'minutes': 30}}

        with self.assertRaises(MixinImplementationError):
            WrongFuncSchedules1().register_tasks()

        class WrongFuncSchedules2(WrongFuncSchedules):
            """Plugin with broken functions.

            This plugin is missing a schedule
            """

            SCHEDULED_TASKS = {'test': {'func': 'test', 'minutes': 30}}

        with self.assertRaises(MixinImplementationError):
            WrongFuncSchedules2().register_tasks()

        class WrongFuncSchedules3(WrongFuncSchedules):
            """Plugin with broken functions.

            This plugin has a broken schedule
            """

            SCHEDULED_TASKS = {
                'test': {'func': 'test', 'schedule': 'XX', 'minutes': 30}
            }

        with self.assertRaises(MixinImplementationError):
            WrongFuncSchedules3().register_tasks()

        class WrongFuncSchedules4(WrongFuncSchedules):
            """Plugin with broken functions.

            This plugin is missing a minute marker for its schedule
            """

            SCHEDULED_TASKS = {'test': {'func': 'test', 'schedule': 'I'}}

        with self.assertRaises(MixinImplementationError):
            WrongFuncSchedules4().register_tasks()
