"""Unit tests for event triggering functions."""

from django.db import transaction
from django.test import TestCase

from django_q.models import OrmQ

from common.models import InvenTreeSetting
from plugin.base.event.events import batch_events, bulk_trigger_event, trigger_event


class BulkEventTriggerTests(TestCase):
    """Unit tests for the bulk_trigger_event function."""

    def test_bulk_trigger_event(self):
        """Test that bulk_trigger_event queues events in a single bulk database write."""
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_EVENTS', True, change_user=None)

        entries = [
            ((idx, idx + 1), {'animal': f'animal_{idx}', 'count': idx})
            for idx in range(10)
        ]

        with self.settings(
            PLUGIN_TESTING_EVENTS=True, PLUGIN_TESTING_EVENTS_ASYNC=True
        ):
            # Start with a blank slate
            OrmQ.objects.all().delete()

            # Queuing all 10 events should only take two database queries:
            # one to check the 'ENABLE_PLUGINS_EVENTS' setting, and one bulk_create
            with self.assertNumQueries(2):
                bulk_trigger_event('test.event', entries)

        self.assertEqual(OrmQ.objects.count(), 10)

        # Read out the pending tasks, and check that the args / kwargs match
        queued_tasks = OrmQ.objects.all().order_by('id')

        for task, (args, kwargs) in zip(queued_tasks, entries, strict=True):
            self.assertEqual(task.func(), 'plugin.base.event.events.register_event')
            self.assertEqual(task.group(), 'plugin')
            self.assertEqual(task.args(), ('test.event', *args))
            self.assertEqual(task.kwargs(), kwargs)


class BatchEventsTests(TestCase):
    """Unit tests for the batch_events() context manager."""

    def setUp(self):
        """Enable plugin events for all tests in this class."""
        super().setUp()
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_EVENTS', True, change_user=None)
        OrmQ.objects.all().delete()

    def test_events_queued_and_flushed_on_commit(self):
        """Events triggered inside batch_events() are queued and flushed as one bulk write on commit."""
        with self.settings(
            PLUGIN_TESTING_EVENTS=True, PLUGIN_TESTING_EVENTS_ASYNC=True
        ):
            with self.captureOnCommitCallbacks(execute=True):
                with transaction.atomic(), batch_events():
                    for idx in range(10):
                        trigger_event('test.event', id=idx, value=f'v{idx}')

                    # Nothing should be queued yet - the batch only flushes on commit
                    self.assertEqual(OrmQ.objects.count(), 0)

        self.assertEqual(OrmQ.objects.count(), 10)

        queued_tasks = OrmQ.objects.all().order_by('id')

        for idx, task in enumerate(queued_tasks):
            self.assertEqual(task.args(), ('test.event',))
            self.assertEqual(task.kwargs(), {'id': idx, 'value': f'v{idx}'})

    def test_events_grouped_by_name(self):
        """Events with different names in the same batch are flushed as separate bulk writes."""
        with self.settings(
            PLUGIN_TESTING_EVENTS=True, PLUGIN_TESTING_EVENTS_ASYNC=True
        ):
            with self.captureOnCommitCallbacks(execute=True):
                with transaction.atomic(), batch_events():
                    for idx in range(5):
                        trigger_event('event.a', id=idx)
                    for idx in range(3):
                        trigger_event('event.b', id=idx)

        self.assertEqual(OrmQ.objects.count(), 8)
        self.assertEqual(
            sum(1 for task in OrmQ.objects.all() if task.args() == ('event.a',)), 5
        )
        self.assertEqual(
            sum(1 for task in OrmQ.objects.all() if task.args() == ('event.b',)), 3
        )

    def test_events_discarded_on_rollback(self):
        """Events queued in a batch are discarded, not fired, if the transaction rolls back."""
        with self.settings(
            PLUGIN_TESTING_EVENTS=True, PLUGIN_TESTING_EVENTS_ASYNC=True
        ):
            with self.captureOnCommitCallbacks(execute=True):
                try:
                    with transaction.atomic(), batch_events():
                        trigger_event('test.event', id=1)
                        raise ValueError('boom')
                except ValueError:
                    pass

        self.assertEqual(OrmQ.objects.count(), 0)

    def test_events_outside_batch_fire_immediately(self):
        """Events triggered outside any batch_events() context are unaffected - fired immediately."""
        with self.settings(
            PLUGIN_TESTING_EVENTS=True, PLUGIN_TESTING_EVENTS_ASYNC=True
        ):
            trigger_event('test.event', id=1)

        # No transaction commit or captureOnCommitCallbacks needed - it was never queued
        self.assertEqual(OrmQ.objects.count(), 1)

    def test_nested_batch_events_share_one_flush(self):
        """A nested batch_events() call reuses the outer batch, rather than flushing twice."""
        with self.settings(
            PLUGIN_TESTING_EVENTS=True, PLUGIN_TESTING_EVENTS_ASYNC=True
        ):
            with self.captureOnCommitCallbacks(execute=True):
                with transaction.atomic(), batch_events():
                    trigger_event('test.event', id=1)
                    with batch_events():
                        trigger_event('test.event', id=2)
                    self.assertEqual(OrmQ.objects.count(), 0)

        self.assertEqual(OrmQ.objects.count(), 2)
