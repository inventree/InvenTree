"""Unit tests for scheduled tasks."""

from django.test import TestCase

from plugin import InvenTreePlugin, registry
from plugin.helpers import MixinImplementationError
from plugin.mixins import ScheduleMixin
from plugin.registry import call_plugin_function


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
        # change the schedule and reregister
        plg.scheduled_tasks['hello']['minutes'] = 15
        plg.register_tasks()

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
        """Check if a function can be called without errors."""
        # Check with right parameters
        self.assertEqual(call_plugin_function('schedule', 'member_func'), False)

        # Check with wrong key
        self.assertEqual(call_plugin_function('does_not_exist', 'member_func'), None)


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
