"""Functional tests for the InvenTree.helpers_db module."""

from unittest import mock

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from company.models import Company, Contact
from InvenTree.helpers_db import bulk_create_and_fetch, bulk_insert_returns_pks
from order.models import PurchaseOrder
from part.models import Part
from stock.models import StockItem


class BulkCreateAndFetchTest(TestCase):
    """Tests for the bulk_create_and_fetch helper function."""

    def test_basic(self):
        """Created items are returned with populated, unique primary keys."""
        company = Company.objects.create(name='ACME')

        items = [Contact(company=company, name=f'Contact {idx}') for idx in range(10)]

        result = bulk_create_and_fetch(Contact, items)

        self.assertEqual(len(result), 10)

        pks = [c.pk for c in result]

        # Every item has a valid, unique primary key
        self.assertTrue(all(pk is not None for pk in pks))
        self.assertEqual(len(pks), len(set(pks)))

        # Returned items exactly match what is actually in the database
        db_pks = set(
            Contact.objects.filter(company=company).values_list('pk', flat=True)
        )
        self.assertEqual(set(pks), db_pks)

        # Temporary bulk-create metadata should have been cleared again
        for contact in Contact.objects.filter(pk__in=pks):
            self.assertIsNone(contact.metadata)

    def test_with_filters(self):
        """Additional filters correctly scope the returned queryset."""
        company_a = Company.objects.create(name='Company A')
        company_b = Company.objects.create(name='Company B')

        items_a = [Contact(company=company_a, name=f'A{i}') for i in range(3)]
        items_b = [Contact(company=company_b, name=f'B{i}') for i in range(4)]

        result_a = bulk_create_and_fetch(
            Contact, items_a, filters={'company': company_a}
        )
        result_b = bulk_create_and_fetch(
            Contact, items_b, filters={'company': company_b}
        )

        self.assertEqual(len(result_a), 3)
        self.assertEqual(len(result_b), 4)

        self.assertTrue(all(c.company_id == company_a.pk for c in result_a))
        self.assertTrue(all(c.company_id == company_b.pk for c in result_b))

    def test_ignores_pre_existing_rows(self):
        """The 'search floor' should exclude pre-existing rows in the table."""
        company = Company.objects.create(name='ACME')

        # Pre-existing item, *not* created via the helper
        Contact.objects.create(company=company, name='Existing')

        items = [Contact(company=company, name=f'New {i}') for i in range(2)]
        result = bulk_create_and_fetch(Contact, items)

        self.assertEqual(len(result), 2)
        self.assertNotIn('Existing', [c.name for c in result])

    def test_preserves_metadata(self):
        """Metadata provided with the input items is retained (in the database and on the items)."""
        company = Company.objects.create(name='ACME')

        items = [
            Contact(company=company, name='With metadata', metadata={'key': 'value'}),
            Contact(company=company, name='Without metadata'),
        ]

        result = bulk_create_and_fetch(Contact, items)

        self.assertEqual(result[0].metadata, {'key': 'value'})
        self.assertIsNone(result[1].metadata)

        # The input items are not left with the temporary bulk-create metadata
        self.assertEqual(items[0].metadata, {'key': 'value'})
        self.assertIsNone(items[1].metadata)

        # No temporary metadata remains in the database
        self.assertFalse(
            Contact.objects.filter(metadata__has_key='bulk_create_id').exists()
        )

    def test_insertion_order(self):
        """Results are returned in insertion order (callers zip them against the input)."""
        company = Company.objects.create(name='ACME')

        names = [f'Contact {idx:03d}' for idx in reversed(range(50))]
        items = [Contact(company=company, name=name) for name in names]

        result = bulk_create_and_fetch(Contact, items)

        self.assertEqual([c.name for c in result], names)

    def test_empty_list(self):
        """Calling with an empty list of items should not raise, and return no items."""
        result = bulk_create_and_fetch(Contact, [])
        self.assertEqual(len(result), 0)

    def test_does_not_mutate_caller_filters(self):
        """The caller-provided 'filters' dict should not be mutated as a side effect."""
        company = Company.objects.create(name='ACME')
        filters = {'company': company}

        items = [Contact(company=company, name='Contact')]
        bulk_create_and_fetch(Contact, items, filters=filters)

    def test_purchase_order(self):
        """The helper works for the PurchaseOrder model."""
        supplier = Company.objects.create(name='Supplier Co', is_supplier=True)

        references = [f'PO-{idx:04d}' for idx in range(10)]

        items = [
            PurchaseOrder(supplier=supplier, reference=ref, description=f'Order {ref}')
            for ref in references
        ]

        result = bulk_create_and_fetch(PurchaseOrder, items)

        self.assertEqual(len(result), 10)

        pks = [o.pk for o in result]
        self.assertTrue(all(pk is not None for pk in pks))
        self.assertEqual(len(pks), len(set(pks)))

        self.assertEqual(
            set(result.values_list('reference', flat=True)), set(references)
        )

        for order in PurchaseOrder.objects.filter(pk__in=pks):
            self.assertIsNone(order.metadata)

    def test_stock_item(self):
        """The helper works for the StockItem model."""
        part = Part.objects.create(name='Widget', description='A widget')

        items = [StockItem(part=part, quantity=idx + 1) for idx in range(10)]

        result = bulk_create_and_fetch(StockItem, items)

        self.assertEqual(len(result), 10)

        pks = [si.pk for si in result]
        self.assertTrue(all(pk is not None for pk in pks))
        self.assertEqual(len(pks), len(set(pks)))

        self.assertEqual(
            sorted(result.values_list('quantity', flat=True)),
            sorted(idx + 1 for idx in range(10)),
        )

        for stock_item in StockItem.objects.filter(pk__in=pks):
            self.assertIsNone(stock_item.metadata)

    def _create_and_count_queries(self, n: int) -> int:
        """Bulk-create 'n' Contact items, and return the number of queries used."""
        company = Company.objects.create(name=f'Company {n}')

        items = [Contact(company=company, name=f'Contact {i}') for i in range(n)]

        with CaptureQueriesContext(connection) as ctx:
            result = bulk_create_and_fetch(Contact, items)

        self.assertEqual(len(result), n)

        MAX_QUERIES = 25 if n > 100 else 10

        self.assertLess(len(ctx.captured_queries), MAX_QUERIES)

        return len(ctx.captured_queries)

    def test_query_count_is_constant(self):
        """The number of queries used should not depend on the number of created items."""
        small_query_count = self._create_and_count_queries(5)
        large_query_count = self._create_and_count_queries(100)

        self.assertEqual(small_query_count, large_query_count)

        # Perform a very large bulk-create - this will be batched
        self._create_and_count_queries(2000)


class BulkCreateAndFetchFallbackTest(BulkCreateAndFetchTest):
    """Run all bulk_create_and_fetch tests against the fallback (metadata lookup) code path.

    This path is used for database backends which do not return primary keys from
    bulk_create() (e.g. MySQL) - forcing it here ensures it is tested on every backend.
    """

    def setUp(self):
        """Force the fallback code path."""
        super().setUp()

        patcher = mock.patch(
            'InvenTree.helpers_db.bulk_insert_returns_pks', return_value=False
        )
        patcher.start()
        self.addCleanup(patcher.stop)


class BulkCreateAndFetchPathTest(TestCase):
    """Tests for the selection of the bulk_create_and_fetch code path."""

    def test_backend_detection(self):
        """The fast path is selected according to the database backend features."""
        self.assertEqual(
            bulk_insert_returns_pks(Contact),
            connection.features.can_return_rows_from_bulk_insert,
        )

    def test_fast_path(self):
        """When primary keys are returned, the temporary metadata is not used at all."""
        if not bulk_insert_returns_pks(Contact):  # pragma: no cover
            self.skipTest('Database backend does not return primary keys')

        company = Company.objects.create(name='ACME')
        items = [Contact(company=company, name=f'Contact {i}') for i in range(5)]

        with CaptureQueriesContext(connection) as ctx:
            result = list(bulk_create_and_fetch(Contact, items))

        self.assertEqual(len(result), 5)

        # Ignore transaction management statements (from @transaction.atomic)
        queries = [
            q['sql']
            for q in ctx.captured_queries
            if 'SAVEPOINT' not in q['sql'].upper()
        ]

        # Insert + fetch only - no metadata tagging / clearing
        self.assertEqual(len(queries), 2, queries)
        self.assertFalse(any('bulk_create_id' in sql for sql in queries))

    def test_fast_path_filters(self):
        """Caller-provided filters are applied on the fast path too."""
        company_a = Company.objects.create(name='A')
        company_b = Company.objects.create(name='B')

        items = [Contact(company=company_a, name='Contact')]

        result = bulk_create_and_fetch(Contact, items, filters={'company': company_b})

        self.assertEqual(len(result), 0)
