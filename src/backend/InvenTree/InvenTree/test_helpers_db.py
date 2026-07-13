"""Functional tests for the InvenTree.helpers_db module."""

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from company.models import Company, Contact
from InvenTree.helpers_db import bulk_create_and_fetch
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

        self.assertEqual(result.count(), 10)

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

        self.assertEqual(result_a.count(), 3)
        self.assertEqual(result_b.count(), 4)

        self.assertTrue(all(c.company_id == company_a.pk for c in result_a))
        self.assertTrue(all(c.company_id == company_b.pk for c in result_b))

    def test_ignores_pre_existing_rows(self):
        """The 'search floor' should exclude pre-existing rows in the table."""
        company = Company.objects.create(name='ACME')

        # Pre-existing item, *not* created via the helper
        Contact.objects.create(company=company, name='Existing')

        items = [Contact(company=company, name=f'New {i}') for i in range(2)]
        result = bulk_create_and_fetch(Contact, items)

        self.assertEqual(result.count(), 2)
        self.assertNotIn('Existing', [c.name for c in result])

    def test_empty_list(self):
        """Calling with an empty list of items should not raise, and return no items."""
        result = bulk_create_and_fetch(Contact, [])
        self.assertEqual(result.count(), 0)

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

        self.assertEqual(result.count(), 10)

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

        self.assertEqual(result.count(), 10)

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

        self.assertEqual(result.count(), n)

        return len(ctx.captured_queries)

    def test_query_count_is_constant(self):
        """The number of queries used should not depend on the number of created items."""
        small_query_count = self._create_and_count_queries(5)
        large_query_count = self._create_and_count_queries(1000)

        self.assertEqual(small_query_count, large_query_count)
        self.assertLess(small_query_count, 8)  # Apply maximum query count ceiling
