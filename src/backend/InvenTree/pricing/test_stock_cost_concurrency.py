"""Concurrency tests for the stock item cost summary.

These tests use real (concurrent) database transactions, and so require a database
backend which supports row-level locking (e.g. PostgreSQL). They are skipped otherwise.
"""

import threading
import time
from decimal import Decimal

from django.db import close_old_connections, connection, connections, transaction
from django.test import TransactionTestCase

from common.models import InvenTreeSetting
from part.models import Part
from pricing.models import CostSource, StockItemCost, StockItemCostEntry
from pricing.status_codes import CostType
from stock.models import StockItem

# Upper bound on any wait, so that a regression cannot hang the test suite
TIMEOUT = 10


class StockItemCostConcurrencyTests(TransactionTestCase):
    """Concurrent cost writes against the same stock item must not lose any cost."""

    def setUp(self):
        """Create a stock item to work with."""
        super().setUp()

        if not connection.features.has_select_for_update:  # pragma: no cover
            self.skipTest('Database backend does not support row-level locking')

        InvenTreeSetting.set_setting('INVENTREE_DEFAULT_CURRENCY', 'USD', None)

        part = Part.objects.create(name='Widget', description='A widget')
        self.item = StockItem.objects.create(part=part, quantity=10)

    def run_concurrently(self, first, second):
        """Run two cost operations in overlapping transactions.

        - 'first' runs inside a transaction, which is held open (uncommitted)
          until 'second' has started
        - 'second' runs in its own transaction, while 'first' is still uncommitted

        Without a common lock, 'second' would calculate its summary without seeing the
        entries written by 'first' - and then overwrite the summary once 'first' commits.
        """
        first_written = threading.Event()
        second_started = threading.Event()
        errors = []

        def run_first():
            try:
                with transaction.atomic():
                    first()
                    first_written.set()

                    # Hold the transaction open while 'second' runs
                    second_started.wait(TIMEOUT)
                    time.sleep(0.5)
            except Exception as exc:  # pragma: no cover
                errors.append(exc)
            finally:
                first_written.set()
                connections.close_all()

        def run_second():
            try:
                first_written.wait(TIMEOUT)
                second_started.set()

                with transaction.atomic():
                    second()
            except Exception as exc:  # pragma: no cover
                errors.append(exc)
            finally:
                connections.close_all()

        threads = [
            threading.Thread(target=run_first),
            threading.Thread(target=run_second),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(TIMEOUT * 2)
            self.assertFalse(
                thread.is_alive(), 'Concurrent cost write did not complete'
            )

        close_old_connections()

        if errors:  # pragma: no cover
            raise errors[0]

    def create(self, value, stock_item=None):
        """Return a callable which creates a cost entry with the given value."""

        def func():
            StockItemCostEntry.objects.create_cost(
                stock_item or self.item,
                CostType.PURCHASE,
                CostSource.MANUAL,
                min_cost=Decimal(value),
                currency='USD',
            )

        return func

    def assertSummary(self, expected, item=None):
        """Check the summary against the *actual* total of the entries."""
        item = item or self.item

        summary = StockItemCost.objects.get(stock_item=item)
        self.assertEqual(summary.min_cost, Decimal(expected))
        self.assertEqual(summary.max_cost, Decimal(expected))
        self.assertFalse(summary.incomplete)

        total = sum(
            entry.converted_min_cost
            for entry in StockItemCostEntry.objects.filter(stock_item=item)
        )
        self.assertEqual(summary.min_cost, total)

    def test_concurrent_create(self):
        """Two entries created concurrently are both included in the summary."""
        self.run_concurrently(self.create(1), self.create(2))
        self.assertSummary(3)

    def test_concurrent_create_existing_summary(self):
        """As above, where the stock item already has a cost summary."""
        self.create(10)()
        self.assertSummary(10)

        self.run_concurrently(self.create(1), self.create(2))
        self.assertSummary(13)

    def test_concurrent_update_and_create(self):
        """An entry edited while another is created - both changes are reflected."""
        self.create(10)()
        entry = StockItemCostEntry.objects.get(stock_item=self.item)

        def update():
            StockItemCostEntry.objects.update_cost(
                StockItemCostEntry.objects.get(pk=entry.pk),
                min_cost=Decimal(4),
                max_cost=Decimal(4),
            )

        self.run_concurrently(update, self.create(2))
        self.assertSummary(6)

    def test_concurrent_delete_and_create(self):
        """An entry deleted while another is created - both changes are reflected."""
        self.create(10)()
        entry = StockItemCostEntry.objects.get(stock_item=self.item)

        def delete():
            StockItemCostEntry.objects.delete_costs([entry])

        self.run_concurrently(delete, self.create(2))
        self.assertSummary(2)

    def test_concurrent_copy_and_create(self):
        """Costs copied onto an item while another cost is added to it."""
        other = StockItem.objects.create(part=self.item.part, quantity=5)
        self.create(7, stock_item=other)()

        def copy():
            StockItemCostEntry.objects.copy_costs([(other, self.item)])

        self.run_concurrently(copy, self.create(2))
        self.assertSummary(9)

        # The source item is unaffected
        self.assertSummary(7, item=other)

    def test_concurrent_bulk_create(self):
        """Bulk-created entries (StockItemCostRecorder) racing a single entry."""

        def bulk():
            StockItemCostEntry.objects.bulk_create_costs([
                {
                    'stock_item': self.item,
                    'cost_type': CostType.PURCHASE,
                    'source': CostSource.MANUAL,
                    'min_cost': Decimal(value),
                    'currency': 'USD',
                }
                for value in (1, 2, 3)
            ])

        self.run_concurrently(self.create(4), bulk)
        self.assertSummary(10)
