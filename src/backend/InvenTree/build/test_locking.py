"""Regression tests for concurrent updates of build orders (and similar "counter" fields).

Background: the 'completed' count of a build order was reset to zero when a user
edited the build order while a background task was completing its outputs. The edit
loaded the build order before the task committed, and then wrote *every* column back
(including the stale 'completed' value) after the task had committed.
"""

import io
import threading
import time
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection, transaction
from django.db.models import F
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse

from rest_framework.test import APIClient

import build.tasks
import InvenTree.helpers_model
from build.models import Build, BuildLine, generate_next_build_reference
from InvenTree.helpers_model import RowLockTimeoutError, lock_row
from InvenTree.models import ProtectedFieldsMixin
from order.models import (
    PurchaseOrderLineItem,
    SalesOrderLineItem,
    TransferOrderLineItem,
)
from part.models import Part
from stock.models import StockItem
from stock.status_codes import StockStatus


def create_build(quantity: int = 100, n_outputs: int = 4, output_quantity: int = 5):
    """Create an issued build order, with a number of (incomplete) build outputs."""
    assembly = Part.objects.create(
        name=f'Locking assembly {generate_next_build_reference()}',
        description='Assembly for build order locking tests',
        assembly=True,
    )

    bo = Build.objects.create(
        reference=generate_next_build_reference(),
        part=assembly,
        quantity=quantity,
        title='Original title',
    )

    bo.issue_build()

    outputs = [
        StockItem.objects.create(
            part=assembly, quantity=output_quantity, is_building=True, build=bo
        )
        for _ in range(n_outputs)
    ]

    return bo, outputs


def run_complete_outputs_task(bo, outputs):
    """Run the background task which completes the provided build outputs."""
    build.tasks.complete_build_outputs(
        bo.pk, [{'output_id': output.pk} for output in outputs], None, StockStatus.OK
    )


class ProtectedFieldsTest(TestCase):
    """Tests for the ProtectedFieldsMixin class (deterministic, no real concurrency)."""

    fixtures = [
        'category',
        'part',
        'location',
        'company',
        'supplier_part',
        'stock',
        'users',
        'bom',
        'build',
        'build_line',
        'order',
        'sales_order',
        'transfer_order',
    ]

    def test_stale_build_save(self):
        """A stale save of a build order must not revert the 'completed' count."""
        bo, outputs = create_build()

        # Another process (e.g. an API request) loads the build order...
        stale = Build.objects.get(pk=bo.pk)

        # ...then the outputs are completed...
        for output in outputs:
            bo.complete_build_output(output, None)

        self.assertEqual(bo.completed, 20)

        # ...and finally the other process saves its (unrelated) change
        stale.title = 'Edited title'
        stale.save()

        bo.refresh_from_db()
        self.assertEqual(bo.title, 'Edited title')
        self.assertEqual(bo.completed, 20)

        # The stale instance does not know about the new value, but a further save is harmless
        self.assertEqual(stale.completed, 0)
        stale.save()

        bo.refresh_from_db()
        self.assertEqual(bo.completed, 20)

    def test_stale_task_save(self):
        """The (full) save performed by the build completion task must not revert the 'completed' count."""
        bo, outputs = create_build()

        stale = Build.objects.get(pk=bo.pk)
        run_complete_outputs_task(bo, outputs)

        # e.g. build.tasks.complete_build / build.tasks.cancel_build
        stale.status = 40
        stale.save()

        bo.refresh_from_db()
        self.assertEqual(bo.status, 40)
        self.assertEqual(bo.completed, 20)

    def test_explicit_change_is_saved(self):
        """A protected field which has been explicitly changed is still written by a full save."""
        bo, _outputs = create_build()

        bo = Build.objects.get(pk=bo.pk)
        bo.completed = 7
        bo.save()

        self.assertEqual(Build.objects.get(pk=bo.pk).completed, 7)

        # The saved value is now the "known" value: it is not written again
        Build.objects.filter(pk=bo.pk).update(completed=12)
        bo.title = 'Another title'
        bo.save()

        self.assertEqual(Build.objects.get(pk=bo.pk).completed, 12)

        # A value which was reloaded from the database is also "known"
        bo.refresh_from_db()
        self.assertEqual(bo.completed, 12)
        Build.objects.filter(pk=bo.pk).update(completed=15)
        bo.save()

        self.assertEqual(Build.objects.get(pk=bo.pk).completed, 15)

    def test_new_instance(self):
        """A protected field is written when the instance is created, and tracked thereafter."""
        bo, _outputs = create_build()

        other = Build.objects.create(
            reference=generate_next_build_reference(),
            part=bo.part,
            quantity=10,
            completed=3,
        )

        self.assertEqual(Build.objects.get(pk=other.pk).completed, 3)

        # The instance which was used to create the row is protected too
        Build.objects.filter(pk=other.pk).update(completed=8)
        other.title = 'Edited title'
        other.save()

        other.refresh_from_db()
        self.assertEqual(other.title, 'Edited title')
        self.assertEqual(other.completed, 8)

    def test_increment_is_not_repeated(self):
        """An F() expression which has been saved must not be applied again by a later save."""
        bo, _outputs = create_build()

        bo = Build.objects.get(pk=bo.pk)
        bo.increment_completed(5)
        self.assertEqual(bo.completed, 5)

        bo.save()
        bo.save()

        self.assertEqual(Build.objects.get(pk=bo.pk).completed, 5)

        # A zero quantity is ignored
        bo.increment_completed(0)
        self.assertEqual(Build.objects.get(pk=bo.pk).completed, 5)

    def test_deferred_field(self):
        """An instance with deferred fields can still be saved."""
        bo, _outputs = create_build()

        Build.objects.filter(pk=bo.pk).update(completed=9)

        for queryset in [Build.objects.defer('completed'), Build.objects.only('title')]:
            partial = queryset.get(pk=bo.pk)
            partial.title = f'Title {queryset.query.deferred_loading[1]}'
            partial.save()

            bo.refresh_from_db()
            self.assertEqual(bo.title, partial.title)
            self.assertEqual(bo.completed, 9)

    def editable_instance(self, model):
        """Return an instance of the model which can be saved (e.g. the order is not locked)."""
        for instance in model.objects.all():
            try:
                instance.save()
                return model.objects.get(pk=instance.pk)
            except ValidationError:
                continue

        self.fail(f'No editable {model.__name__} found')  # pragma: no cover

    def test_update_fields(self):
        """An unchanged protected field is not written, even if it is named in update_fields."""
        bo, _outputs = create_build()

        stale = Build.objects.get(pk=bo.pk)
        Build.objects.filter(pk=bo.pk).update(completed=11)

        stale.title = 'Edited title'
        stale.save(update_fields=['title', 'completed'])

        bo.refresh_from_db()
        self.assertEqual(bo.title, 'Edited title')
        self.assertEqual(bo.completed, 11)

        # Nothing to write at all
        stale.save(update_fields=['completed'])
        self.assertEqual(Build.objects.get(pk=bo.pk).completed, 11)

        # A changed value is written
        stale.completed = 4
        stale.save(update_fields=['completed'])
        self.assertEqual(Build.objects.get(pk=bo.pk).completed, 4)

        # Identical increments are each applied
        for _ in range(2):
            stale.completed = F('completed') + 3
            stale.save(update_fields=['completed'])

        self.assertEqual(Build.objects.get(pk=bo.pk).completed, 10)

    def test_protected_models(self):
        """Each model with protected fields must survive a stale save."""
        models = {
            Build: 'completed',
            BuildLine: 'consumed',
            PurchaseOrderLineItem: 'received',
            SalesOrderLineItem: 'shipped',
            TransferOrderLineItem: 'transferred',
        }

        for model, field in models.items():
            with self.subTest(model=model.__name__):
                self.assertTrue(issubclass(model, ProtectedFieldsMixin))
                self.assertEqual(model.PROTECTED_FIELDS, (field,))

                # The mixin must come after any other class which overrides save()
                mro = model.__mro__
                self.assertEqual(
                    [cls for cls in mro if 'save' in vars(cls)][-2],
                    ProtectedFieldsMixin,
                )

                instance = self.editable_instance(model)

                stale = model.objects.get(pk=instance.pk)
                value = getattr(stale, field) + 3

                # A concurrent process updates the counter
                model.objects.filter(pk=instance.pk).update(**{field: value})

                # A stale save does not revert it
                stale.save()
                instance.refresh_from_db()
                self.assertEqual(getattr(instance, field), value)

                # An explicit change is written
                setattr(instance, field, value + 1)
                instance.save()
                self.assertEqual(
                    getattr(model.objects.get(pk=instance.pk), field), value + 1
                )


class CheckBuildCompletedCommandTest(TestCase):
    """Tests for the 'check_build_completed' management command."""

    def run_command(self, *args) -> str:
        """Run the management command, and return the output."""
        out = io.StringIO()
        call_command('check_build_completed', *args, stdout=out)
        return out.getvalue()

    def test_command(self):
        """A 'completed' count which was overwritten is detected, and can be repaired."""
        bo, outputs = create_build()
        other, other_outputs = create_build(n_outputs=1)

        run_complete_outputs_task(bo, outputs)
        run_complete_outputs_task(other, other_outputs)

        output = self.run_command()
        self.assertIn('0 mismatched', output)

        # Overwrite the count, without recording the change (as per a stale save)
        Build.objects.filter(pk=bo.pk).update(completed=0)

        for source in ['audit', 'outputs']:
            output = self.run_command('--source', source)
            self.assertIn(f'{bo.reference} (pk={bo.pk}): completed=0', output)
            self.assertIn('audit history=20, completed outputs=20', output)
            self.assertIn('1 mismatched, 0 updated', output)
            self.assertNotIn(other.reference, output)

        # Nothing has been changed (yet)
        bo.refresh_from_db()
        self.assertEqual(bo.completed, 0)

        # Limit to a particular build order (by reference, or by ID)
        self.assertIn('0 mismatched', self.run_command(other.reference))
        self.assertIn('1 mismatched', self.run_command(str(bo.pk)))

        output = self.run_command('--fix', bo.reference)
        self.assertIn('updated: completed=20', output)
        self.assertIn('1 mismatched, 1 updated', output)

        bo.refresh_from_db()
        self.assertEqual(bo.completed, 20)

        self.assertIn('0 mismatched', self.run_command())

    def test_fix_from_outputs(self):
        """The count can be repaired from the completed outputs, if the audit history is wrong."""
        bo, outputs = create_build()
        run_complete_outputs_task(bo, outputs)

        # An (audited) write of the wrong value
        bo.completed = 3
        bo.save()

        self.assertIn('0 mismatched', self.run_command())

        output = self.run_command('--source', 'outputs', '--fix')
        self.assertIn('1 mismatched, 1 updated', output)

        bo.refresh_from_db()
        self.assertEqual(bo.completed, 20)

    def test_invalid_build(self):
        """An unknown build order is reported."""
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            self.run_command('BO-does-not-exist')


class ThreadedTestMixin:
    """Helpers for tests which run code in multiple threads (each with its own database connection)."""

    def run_thread(self, func, *args) -> threading.Thread:
        """Run the provided function in a new thread, recording any exception."""

        def target():
            try:
                func(*args)
            except Exception as exc:  # pragma: no cover - surfaced via errors list
                self.errors.append(exc)
            finally:
                connection.close()

        thread = threading.Thread(target=target)
        thread.start()
        self.threads.append(thread)

        return thread

    def join_threads(self):
        """Wait for all threads to complete, and check that no errors occurred."""
        for thread in self.threads:
            thread.join(timeout=20)
            self.assertFalse(thread.is_alive())

        self.assertEqual(self.errors, [])

    def setUp(self):
        """Reset the thread state."""
        super().setUp()
        self.threads = []
        self.errors = []

    def hold_row_lock(self, model, pk, hold: threading.Event, **changes):
        """Lock a database row in another thread, until the 'hold' event is set.

        Any 'changes' are written to the row (and committed) when the lock is released.
        Returns once the lock has been acquired.
        """
        locked = threading.Event()

        def holder():
            with transaction.atomic():
                model.objects.select_for_update().get(pk=pk)
                locked.set()
                hold.wait(timeout=15)

                if changes:
                    model.objects.filter(pk=pk).update(**changes)

        self.run_thread(holder)
        self.assertTrue(locked.wait(timeout=5))


@skipUnlessDBFeature('has_select_for_update')
class BuildCompletedConcurrencyTest(ThreadedTestMixin, TransactionTestCase):
    """Cross-transaction tests for the 'completed' count of a build order.

    These tests use real threads (each with its own database connection),
    to reproduce the interleaving of a background task and a concurrent edit.
    """

    def pause_task_before_commit(self):
        """Patch the output completion task so that it pauses just before it commits.

        At this point the task has updated (and so holds a lock on) the build order row.

        Returns:
            A tuple of (context manager, 'paused' event, 'resume' event)
        """
        paused = threading.Event()
        resume = threading.Event()

        original = Build.increment_completed

        def increment_and_pause(bo, quantity):
            original(bo, quantity)
            paused.set()
            resume.wait(timeout=15)

        patcher = mock.patch.object(Build, 'increment_completed', increment_and_pause)

        return patcher, paused, resume

    def test_edit_during_output_completion(self):
        """A build order which is saved while its outputs are being completed keeps its 'completed' count.

        This reproduces the reported sequence of events:

        1. The edit loads the build order (completed = 0)
        2. The task completes the outputs, but has not yet committed
        3. The edit saves the build order: the write blocks on the row lock held by the task
        4. The task commits (completed = 20)
        5. The edit is written - and must not reset the 'completed' count
        """
        bo, outputs = create_build()

        patcher, paused, resume = self.pause_task_before_commit()

        # 1. The edit loads the build order
        stale = Build.objects.get(pk=bo.pk)

        saved = threading.Event()

        def edit():
            stale.title = 'Edited title'
            stale.save()
            saved.set()

        with patcher:
            # 2. The task completes the outputs (but does not commit)
            self.run_thread(run_complete_outputs_task, bo, outputs)
            self.assertTrue(paused.wait(timeout=10))

            # The uncommitted count is not visible to anyone else
            self.assertEqual(Build.objects.get(pk=bo.pk).completed, 0)

            # 3. The edit is saved, and blocks on the row lock
            self.run_thread(edit)
            self.assertFalse(saved.wait(timeout=0.5))

            # 4. The task commits, which also unblocks the edit
            resume.set()
            self.join_threads()

        self.assertTrue(saved.is_set())

        bo.refresh_from_db()
        self.assertEqual(bo.title, 'Edited title')
        self.assertEqual(bo.completed, 20)

        for output in outputs:
            output.refresh_from_db()
            self.assertFalse(output.is_building)

    def test_concurrent_output_completion(self):
        """Tasks which complete different outputs of the same build order at the same time are all counted."""
        bo, outputs = create_build(n_outputs=6)

        barrier = threading.Barrier(3, timeout=10)

        def run(task_outputs):
            barrier.wait()
            run_complete_outputs_task(bo, task_outputs)

        for idx in range(3):
            self.run_thread(run, outputs[idx * 2 : idx * 2 + 2])

        self.join_threads()

        bo.refresh_from_db()
        self.assertEqual(bo.completed, 30)

    def test_duplicate_output_completion(self):
        """The same task delivered twice (and running concurrently) only counts each output once."""
        bo, outputs = create_build()

        barrier = threading.Barrier(2, timeout=10)

        def run():
            barrier.wait()
            run_complete_outputs_task(bo, outputs)

        self.run_thread(run)
        self.run_thread(run)
        self.join_threads()

        bo.refresh_from_db()
        self.assertEqual(bo.completed, 20)

    def test_complete_build_during_output_completion(self):
        """The task which completes the build order must not revert the count of a concurrent output completion."""
        bo, outputs = create_build(quantity=20)
        user = get_user_model().objects.create(username='locking-user')

        patcher, paused, resume = self.pause_task_before_commit()

        with patcher:
            self.run_thread(run_complete_outputs_task, bo, outputs)
            self.assertTrue(paused.wait(timeout=10))

            # This task waits for the build order row, which is locked by the task above
            self.run_thread(build.tasks.complete_build, bo.pk, user.pk)
            time.sleep(0.5)

            resume.set()
            self.join_threads()

        bo.refresh_from_db()
        self.assertEqual(bo.status, 40)
        self.assertEqual(bo.completed, 20)

    def test_lock_row(self):
        """The lock_row() helper gives up if the row is locked by another transaction."""
        bo, _outputs = create_build()

        # No such row
        with transaction.atomic():
            self.assertFalse(lock_row(Build, bo.pk + 1000))

        release = threading.Event()
        self.hold_row_lock(Build, bo.pk, release)

        try:
            start = time.monotonic()

            with transaction.atomic():
                with self.assertRaises(RowLockTimeoutError):
                    lock_row(Build, bo.pk, timeout=0.3)

                # The transaction is still usable after the failed attempt
                self.assertTrue(Build.objects.filter(pk=bo.pk).exists())

            self.assertGreaterEqual(time.monotonic() - start, 0.3)
        finally:
            release.set()

        self.join_threads()

        # The lock is available again
        with transaction.atomic():
            self.assertTrue(lock_row(Build, bo.pk, timeout=0.3))


@skipUnlessDBFeature('has_select_for_update')
class BuildUpdateLockingAPITest(ThreadedTestMixin, TransactionTestCase):
    """Cross-transaction tests for updating a build order via the API."""

    def setUp(self):
        """Create an authenticated API client."""
        super().setUp()

        user = get_user_model().objects.create(
            username='locking-admin', is_superuser=True, is_staff=True
        )

        self.client = APIClient()
        self.client.force_authenticate(user=user)

        self.bo, self.outputs = create_build()
        self.url = reverse('api-build-detail', kwargs={'pk': self.bo.pk})

    def test_update_locked_build(self):
        """An update is rejected (409) if the build order is locked by a long-running process."""
        release = threading.Event()
        self.hold_row_lock(Build, self.bo.pk, release)

        try:
            with mock.patch.object(InvenTree.helpers_model, 'ROW_LOCK_TIMEOUT', 0.3):
                response = self.client.patch(
                    self.url, {'title': 'Edited title'}, format='json'
                )

                self.assertEqual(response.status_code, 409)
                self.assertIn('currently being updated', response.data['detail'])

                # Reading the build order is not affected
                self.assertEqual(self.client.get(self.url).status_code, 200)
        finally:
            release.set()

        self.join_threads()

        # Nothing was written
        self.bo.refresh_from_db()
        self.assertEqual(self.bo.title, 'Original title')

        # The update succeeds once the lock has been released
        response = self.client.patch(self.url, {'title': 'Edited title'}, format='json')
        self.assertEqual(response.status_code, 200)

        self.bo.refresh_from_db()
        self.assertEqual(self.bo.title, 'Edited title')

    def test_update_waits_for_lock(self):
        """An update which waits (briefly) for a lock is applied to the *latest* data.

        The other process changes fields which are not otherwise protected: if the
        build order had been read before the lock was acquired, the update
        would write the stale values back.
        """
        release = threading.Event()
        self.hold_row_lock(
            Build, self.bo.pk, release, priority=5, batch='ABC', completed=15
        )

        # Release the lock while the request is waiting for it
        timer = threading.Timer(0.5, release.set)
        timer.start()

        response = self.client.patch(self.url, {'title': 'Edited title'}, format='json')
        timer.join()

        self.assertEqual(response.status_code, 200)
        self.join_threads()

        # The response reflects the latest data
        self.assertEqual(response.data['priority'], 5)
        self.assertEqual(response.data['completed'], 15)

        self.bo.refresh_from_db()
        self.assertEqual(self.bo.title, 'Edited title')
        self.assertEqual(self.bo.priority, 5)
        self.assertEqual(self.bo.batch, 'ABC')
        self.assertEqual(self.bo.completed, 15)

    def test_update_during_output_completion(self):
        """Editing a build order (via the API) while its outputs are being completed.

        The request is rejected while the task holds the build order row,
        and the 'completed' count is intact afterwards.
        """
        paused = threading.Event()
        resume = threading.Event()

        original = Build.increment_completed

        def increment_and_pause(bo, quantity):
            original(bo, quantity)
            paused.set()
            resume.wait(timeout=15)

        try:
            with mock.patch.object(Build, 'increment_completed', increment_and_pause):
                self.run_thread(run_complete_outputs_task, self.bo, self.outputs)
                self.assertTrue(paused.wait(timeout=10))

                with mock.patch.object(
                    InvenTree.helpers_model, 'ROW_LOCK_TIMEOUT', 0.3
                ):
                    response = self.client.patch(
                        self.url, {'title': 'Edited title'}, format='json'
                    )

                self.assertEqual(response.status_code, 409)

                resume.set()
                self.join_threads()
        finally:
            resume.set()

        response = self.client.patch(self.url, {'title': 'Edited title'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['completed'], 20)

        self.bo.refresh_from_db()
        self.assertEqual(self.bo.title, 'Edited title')
        self.assertEqual(self.bo.completed, 20)

    def test_update_not_found(self):
        """Updating a build order which does not exist returns a 404."""
        url = reverse('api-build-detail', kwargs={'pk': self.bo.pk + 1000})
        response = self.client.patch(url, {'title': 'Edited title'}, format='json')
        self.assertEqual(response.status_code, 404)
