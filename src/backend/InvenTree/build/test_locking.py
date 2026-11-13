"""Regression tests for concurrent updates of build orders (and similar "counter" fields).

Background: the 'completed' count of a build order was reset to zero when a user
edited the build order while a background task was completing its outputs. The edit
loaded the build order before the task committed, and then wrote *every* column back
(including the stale 'completed' value) after the task had committed.
"""

import threading
import time
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse

from rest_framework.test import APIClient

import build.tasks
import InvenTree.helpers_model
from build.models import Build, generate_next_build_reference
from build.status_codes import BuildStatus
from company.models import Company
from InvenTree.helpers_model import RowLockTimeoutError, lock_row
from order.models import (
    PurchaseOrder,
    ReturnOrder,
    SalesOrder,
    SalesOrderShipment,
    TransferOrder,
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


@skipUnlessDBFeature('has_select_for_update')
class ActionLockingAPITest(ThreadedTestMixin, TransactionTestCase):
    """Cross-transaction tests for "action" endpoints, which act upon an existing object.

    These endpoints (e.g. "hold" a build order) load the object, and then save it again
    in full. The row must be locked *before* the object is loaded, otherwise the save
    reverts any change which was committed in the meantime.
    """

    def setUp(self):
        """Create an authenticated API client."""
        super().setUp()

        user = get_user_model().objects.create(
            username='locking-admin', is_superuser=True, is_staff=True
        )

        self.client = APIClient()
        self.client.force_authenticate(user=user)

    def post(self, url_name: str, pk: int, data=None):
        """POST to the named action endpoint."""
        url = reverse(url_name, kwargs={'pk': pk})
        return self.client.post(url, data or {}, format='json')

    def assert_locked(self, model, pk, url_name: str, url_pk=None, data=None):
        """Assert that the action is rejected (409) while the specified row is locked."""
        release = threading.Event()
        self.hold_row_lock(model, pk, release)

        try:
            with mock.patch.object(InvenTree.helpers_model, 'ROW_LOCK_TIMEOUT', 0.3):
                response = self.post(url_name, url_pk or pk, data)
        finally:
            release.set()

        self.join_threads()
        self.threads.clear()

        self.assertEqual(response.status_code, 409, f'{url_name}: {response.data}')
        self.assertIn('currently being updated', response.data['detail'])

    def test_build_hold_locked(self):
        """A build order cannot be placed on hold while it is locked by another process."""
        bo, _outputs = create_build()

        self.assert_locked(Build, bo.pk, 'api-build-hold')

        # Nothing was changed
        bo.refresh_from_db()
        self.assertEqual(bo.status, BuildStatus.PRODUCTION.value)

        # The action succeeds once the lock has been released
        response = self.post('api-build-hold', bo.pk)
        self.assertEqual(response.status_code, 201)

        bo.refresh_from_db()
        self.assertEqual(bo.status, BuildStatus.ON_HOLD.value)

    def test_build_hold_waits_for_lock(self):
        """An action which waits (briefly) for a lock is applied to the *latest* data.

        The other process changes fields which are not otherwise protected: if the
        build order had been read before the lock was acquired, the action
        (which saves the entire build order) would write the stale values back.
        """
        bo, _outputs = create_build()

        release = threading.Event()
        self.hold_row_lock(Build, bo.pk, release, priority=5, batch='ABC', completed=15)

        # Release the lock while the request is waiting for it
        timer = threading.Timer(0.5, release.set)
        timer.start()

        response = self.post('api-build-hold', bo.pk)
        timer.join()

        self.assertEqual(response.status_code, 201)
        self.join_threads()

        bo.refresh_from_db()
        self.assertEqual(bo.status, BuildStatus.ON_HOLD.value)
        self.assertEqual(bo.priority, 5)
        self.assertEqual(bo.batch, 'ABC')
        self.assertEqual(bo.completed, 15)

    def test_build_hold_during_output_completion(self):
        """Placing a build order on hold while its outputs are being completed.

        The request is rejected while the task holds the build order row,
        and the 'completed' count is intact afterwards.
        """
        bo, outputs = create_build()

        paused = threading.Event()
        resume = threading.Event()

        original = Build.increment_completed

        def increment_and_pause(build_order, quantity):
            original(build_order, quantity)
            paused.set()
            resume.wait(timeout=15)

        try:
            with mock.patch.object(Build, 'increment_completed', increment_and_pause):
                self.run_thread(run_complete_outputs_task, bo, outputs)
                self.assertTrue(paused.wait(timeout=10))

                with mock.patch.object(
                    InvenTree.helpers_model, 'ROW_LOCK_TIMEOUT', 0.3
                ):
                    response = self.post('api-build-hold', bo.pk)

                self.assertEqual(response.status_code, 409)

                resume.set()
                self.join_threads()
        finally:
            resume.set()

        response = self.post('api-build-hold', bo.pk)
        self.assertEqual(response.status_code, 201)

        bo.refresh_from_db()
        self.assertEqual(bo.status, BuildStatus.ON_HOLD.value)
        self.assertEqual(bo.completed, 20)

    def test_build_actions_locked(self):
        """Every build order action is rejected while the build order is locked."""
        bo, _outputs = create_build()

        for url_name in [
            'api-build-issue',
            'api-build-hold',
            'api-build-cancel',
            'api-build-finish',
            'api-build-allocate',
            'api-build-auto-allocate',
            'api-build-consume',
            'api-build-output-create',
            'api-build-output-complete',
            'api-build-output-scrap',
            'api-build-output-delete',
        ]:
            with self.subTest(url=url_name):
                self.assert_locked(Build, bo.pk, url_name)

    def test_barcode_assign(self):
        """Assigning (or removing) a barcode saves the entire object, so the row must be locked."""
        bo, _outputs = create_build()

        url = reverse('api-barcode-link')
        data = {'barcode': 'locking-test-barcode', 'build': bo.pk}

        release = threading.Event()
        self.hold_row_lock(Build, bo.pk, release)

        try:
            with mock.patch.object(InvenTree.helpers_model, 'ROW_LOCK_TIMEOUT', 0.3):
                response = self.client.post(url, data, format='json')
        finally:
            release.set()

        self.join_threads()
        self.threads.clear()

        self.assertEqual(response.status_code, 409)

        bo.refresh_from_db()
        self.assertEqual(bo.barcode_data, '')

        # Once the lock is available, the barcode is assigned to the *latest* data
        for url_name, expected in [
            ('api-barcode-link', 'locking-test-barcode'),
            ('api-barcode-unlink', ''),
        ]:
            completed = bo.completed + 5

            release = threading.Event()
            self.hold_row_lock(Build, bo.pk, release, completed=completed)

            timer = threading.Timer(0.5, release.set)
            timer.start()

            response = self.client.post(reverse(url_name), data, format='json')
            timer.join()

            self.join_threads()
            self.threads.clear()

            self.assertEqual(response.status_code, 200, response.data)

            bo.refresh_from_db()
            self.assertEqual(bo.barcode_data, expected)
            self.assertEqual(bo.completed, completed)

    def test_build_action_not_found(self):
        """An action against a build order which does not exist returns a 404."""
        response = self.post('api-build-hold', 9999)
        self.assertEqual(response.status_code, 404)

    def test_order_actions_locked(self):
        """Order actions are rejected while the order is locked."""
        company = Company.objects.create(
            name='Locking company', is_customer=True, is_supplier=True
        )

        orders = {
            SalesOrder: (
                SalesOrder.objects.create(reference='SO-9990', customer=company),
                ['api-so-hold', 'api-so-issue', 'api-so-cancel', 'api-so-complete'],
            ),
            ReturnOrder: (
                ReturnOrder.objects.create(reference='RMA-9990', customer=company),
                ['api-ro-hold', 'api-return-order-issue', 'api-return-order-cancel'],
            ),
            TransferOrder: (
                TransferOrder.objects.create(reference='TO-9990'),
                ['api-transfer-order-hold', 'api-transfer-order-issue'],
            ),
            PurchaseOrder: (
                PurchaseOrder.objects.create(reference='PO-9990', supplier=company),
                ['api-po-hold', 'api-po-issue', 'api-po-cancel', 'api-po-receive'],
            ),
        }

        for model, (order, url_names) in orders.items():
            for url_name in url_names:
                with self.subTest(url=url_name):
                    self.assert_locked(model, order.pk, url_name)

        # A transition is applied to the latest data once the lock is available
        po, _url_names = orders[PurchaseOrder]

        release = threading.Event()
        self.hold_row_lock(PurchaseOrder, po.pk, release, description='Changed')

        timer = threading.Timer(0.5, release.set)
        timer.start()

        response = self.post('api-po-issue', po.pk)
        timer.join()
        self.join_threads()

        self.assertEqual(response.status_code, 201)

        po.refresh_from_db()
        self.assertEqual(po.description, 'Changed')
        self.assertEqual(po.status, 20)

    def test_shipment_complete_locked(self):
        """A shipment cannot be completed while it is locked."""
        company = Company.objects.create(name='Locking customer', is_customer=True)
        order = SalesOrder.objects.create(reference='SO-9991', customer=company)
        shipment = SalesOrderShipment.objects.create(order=order, reference='1')

        self.assert_locked(SalesOrderShipment, shipment.pk, 'api-so-shipment-ship')

    def test_stock_item_actions_locked(self):
        """Stock item actions are rejected while the stock item is locked."""
        part = Part.objects.create(
            name='Locking part', description='Part for locking tests'
        )
        item = StockItem.objects.create(part=part, quantity=10)

        for url_name in [
            'api-stock-item-serialize',
            'api-stock-item-install',
            'api-stock-item-uninstall',
            'api-stock-item-convert',
        ]:
            with self.subTest(url=url_name):
                self.assert_locked(StockItem, item.pk, url_name)
