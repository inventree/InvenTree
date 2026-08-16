"""Unit tests for the pricing API."""

from django.db import IntegrityError, transaction
from django.urls import reverse

from djmoney.money import Money

from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from stock.models import StockItem

from .models import StockItemCost, StockItemCostEntry
from .status_codes import CostType


class PricingAPITestCase(InvenTreeAPITestCase):
    """Base class for pricing API tests."""

    fixtures = ['category', 'part', 'location', 'stock']

    roles = ['pricing.view', 'pricing.add', 'pricing.delete', 'stock.view']

    @classmethod
    def setUpTestData(cls):
        """Initialize test data for the pricing API tests."""
        super().setUpTestData()

        cls.part = Part.objects.get(pk=1)
        cls.stock_item = StockItem.objects.get(pk=1)

    def entry_list_url(self):
        """Return the URL for the StockItemCostEntry list endpoint."""
        return reverse('api-pricing-cost-entry-list')

    def entry_detail_url(self, pk):
        """Return the URL for a specific StockItemCostEntry detail endpoint."""
        return reverse('api-pricing-cost-entry-detail', kwargs={'pk': pk})

    def status_url(self):
        """Return the URL for the CostType status code endpoint."""
        return reverse('api-pricing-cost-entry-status-codes')

    def cost_list_url(self):
        """Return the URL for the (read-only) StockItemCost summary list endpoint."""
        return reverse('api-pricing-cost-list')

    def cost_detail_url(self, pk):
        """Return the URL for a specific (read-only) StockItemCost summary detail endpoint."""
        return reverse('api-pricing-cost-detail', kwargs={'pk': pk})


class StockItemCostEntryListTest(PricingAPITestCase):
    """Tests for listing and creating StockItemCostEntry objects."""

    def test_list_empty(self):
        """An empty list should be returned if no cost entries exist."""
        response = self.get(self.entry_list_url())
        self.assertEqual(response.data, [])

    def test_create(self):
        """Test creation of a new StockItemCostEntry via the API."""
        data = {
            'stock_item': self.stock_item.pk,
            'cost_type': CostType.PURCHASE.value,
            'min_cost': '1.500',
            'min_cost_currency': 'USD',
            'max_cost': '2.500',
            'max_cost_currency': 'USD',
            'notes': 'Some notes',
        }

        response = self.post(self.entry_list_url(), data)

        entry = StockItemCostEntry.objects.get(pk=response.data['pk'])

        # The 'user' field should be automatically populated from the request
        self.assertEqual(entry.user, self.user)

        self.assertEqual(entry.stock_item, self.stock_item)
        self.assertEqual(entry.cost_type, CostType.PURCHASE.value)
        self.assertEqual(entry.min_cost, Money('1.5', 'USD'))
        self.assertEqual(entry.max_cost, Money('2.5', 'USD'))
        self.assertEqual(entry.notes, 'Some notes')

    def test_create_updates_existing_entry(self):
        """Posting again for the same (stock_item, cost_type) pair updates the existing entry."""
        first = StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
            notes='Original',
        )

        data = {
            'stock_item': self.stock_item.pk,
            'cost_type': CostType.PURCHASE.value,
            'min_cost': '3.000',
            'min_cost_currency': 'USD',
            'max_cost': '4.000',
            'max_cost_currency': 'USD',
            'notes': 'Updated',
        }

        response = self.post(self.entry_list_url(), data, expected_code=200)

        # No new entry should have been created - the existing one is updated
        self.assertEqual(
            StockItemCostEntry.objects.filter(
                stock_item=self.stock_item, cost_type=CostType.PURCHASE.value
            ).count(),
            1,
        )

        first.refresh_from_db()
        self.assertEqual(response.data['pk'], first.pk)
        self.assertEqual(first.min_cost, Money('3', 'USD'))
        self.assertEqual(first.max_cost, Money('4', 'USD'))
        self.assertEqual(first.notes, 'Updated')

    def test_create_no_permission(self):
        """A user without 'pricing.add' permission cannot create a cost entry."""
        self.clearRoles()
        self.assignRole('pricing.view')

        data = {'stock_item': self.stock_item.pk, 'cost_type': CostType.PURCHASE.value}

        self.post(self.entry_list_url(), data, expected_code=403)

    def test_list_no_permission(self):
        """A user without 'pricing.view' permission cannot list cost entries."""
        self.clearRoles()

        self.get(self.entry_list_url(), expected_code=403)

    def test_list_and_filter(self):
        """Test listing and filtering of StockItemCostEntry objects."""
        other_item = StockItem.objects.exclude(part=self.stock_item.part).first()

        StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.LANDED.value,
            min_cost=Money(3, 'USD'),
            max_cost=Money(4, 'USD'),
        )

        StockItemCostEntry.objects.create(
            stock_item=other_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(5, 'USD'),
            max_cost=Money(6, 'USD'),
        )

        # Filter by linked stock item
        response = self.get(self.entry_list_url(), {'stock_item': self.stock_item.pk})
        self.assertEqual(len(response.data), 2)

        # Filter by cost type
        response = self.get(self.entry_list_url(), {'cost_type': CostType.LANDED.value})
        self.assertEqual(len(response.data), 1)

        # No filters - expect all three entries
        response = self.get(self.entry_list_url())
        self.assertEqual(len(response.data), 3)


class StockItemCostEntryDetailTest(PricingAPITestCase):
    """Tests for retrieving, updating and deleting individual StockItemCostEntry objects."""

    @classmethod
    def setUpTestData(cls):
        """Initialize test data for the pricing API detail tests."""
        super().setUpTestData()

        cls.entry = StockItemCostEntry.objects.create(
            stock_item=cls.stock_item,
            cost_type=CostType.MANUAL.value,
            min_cost=Money(10, 'USD'),
            max_cost=Money(20, 'USD'),
            notes='Test cost entry',
        )

    def test_retrieve(self):
        """Test that a single StockItemCostEntry can be retrieved."""
        response = self.get(self.entry_detail_url(self.entry.pk))

        self.assertEqual(response.data['pk'], self.entry.pk)
        self.assertEqual(response.data['stock_item'], self.stock_item.pk)
        self.assertEqual(response.data['notes'], 'Test cost entry')

    def test_retrieve_optional_fields(self):
        """Test that optional detail fields can be requested."""
        self.run_output_test(
            self.entry_detail_url(self.entry.pk), ['stock_item_detail', 'user_detail']
        )

    def test_update(self):
        """A StockItemCostEntry can be updated in place, given 'change' permission."""
        self.assignRole('pricing.change')

        response = self.patch(
            self.entry_detail_url(self.entry.pk),
            {'notes': 'Updated'},
            expected_code=200,
        )
        self.assertEqual(response.data['notes'], 'Updated')

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.notes, 'Updated')
        self.assertEqual(self.entry.user, self.user)

    def test_update_no_permission(self):
        """A user without 'pricing.change' permission cannot update a cost entry."""
        self.clearRoles()
        self.assignRole('pricing.view')

        self.patch(
            self.entry_detail_url(self.entry.pk),
            {'notes': 'Updated'},
            expected_code=403,
        )

    def test_delete(self):
        """Test that a StockItemCostEntry can be deleted."""
        self.delete(self.entry_detail_url(self.entry.pk))
        self.assertFalse(StockItemCostEntry.objects.filter(pk=self.entry.pk).exists())

    def test_delete_no_permission(self):
        """A user without 'pricing.delete' permission cannot delete a cost entry."""
        self.clearRoles()
        self.assignRole('pricing.view')

        self.delete(self.entry_detail_url(self.entry.pk), expected_code=403)

    def test_cascade_delete_with_stock_item(self):
        """Deleting the linked StockItem should also delete any associated cost entries."""
        pk = self.entry.pk

        self.stock_item.delete()

        self.assertFalse(StockItemCostEntry.objects.filter(pk=pk).exists())


class StockItemCostEntryModelTest(PricingAPITestCase):
    """Tests for the StockItemCostEntry model itself."""

    def test_unique_stock_item_cost_type(self):
        """Only one entry may exist per (stock_item, cost_type) pair."""
        StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            StockItemCostEntry.objects.create(
                stock_item=self.stock_item,
                cost_type=CostType.PURCHASE.value,
                min_cost=Money(3, 'USD'),
                max_cost=Money(4, 'USD'),
            )


class StockItemCostEntryStatusTest(PricingAPITestCase):
    """Tests for the CostType status code endpoint."""

    def test_status_codes(self):
        """Test that the CostType status codes are correctly reported."""
        response = self.get(self.status_url())

        self.assertEqual(response.data['status_class'], 'CostType')

        values = response.data['values']

        for name in ['PURCHASE', 'LANDED', 'MANUFACTURING', 'MANUAL', 'SYSTEM']:
            self.assertIn(name, values)


class StockItemCostRecalculationTest(PricingAPITestCase):
    """Tests that the StockItemCost summary is kept in sync with StockItemCostEntry records."""

    def test_no_entries_no_summary(self):
        """A stock item with no cost entries should have no cached summary."""
        self.assertFalse(
            StockItemCost.objects.filter(stock_item=self.stock_item).exists()
        )

    def test_summary_created_on_first_entry(self):
        """Creating the first cost entry for a stock item creates its summary."""
        StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary.min_cost, Money(1, 'USD'))
        self.assertEqual(summary.max_cost, Money(2, 'USD'))

    def test_summary_sums_multiple_entries(self):
        """The summary should be the sum of every associated cost entry."""
        StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.LANDED.value,
            min_cost=Money('1.5', 'USD'),
            max_cost=Money('2.5', 'USD'),
        )

        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary.min_cost, Money('2.5', 'USD'))
        self.assertEqual(summary.max_cost, Money('4.5', 'USD'))

    def test_summary_updates_on_entry_update(self):
        """Updating a cost entry should update the cached summary."""
        entry = StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        entry.min_cost = Money(10, 'USD')
        entry.max_cost = Money(20, 'USD')
        entry.save()

        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary.min_cost, Money(10, 'USD'))
        self.assertEqual(summary.max_cost, Money(20, 'USD'))

    def test_summary_removed_when_last_entry_deleted(self):
        """Deleting the only cost entry for a stock item should remove its summary."""
        entry = StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        self.assertTrue(
            StockItemCost.objects.filter(stock_item=self.stock_item).exists()
        )

        entry.delete()

        self.assertFalse(
            StockItemCost.objects.filter(stock_item=self.stock_item).exists()
        )

    def test_summary_updates_when_one_of_several_entries_deleted(self):
        """Deleting one of several entries should recalculate (not remove) the summary."""
        StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        landed = StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.LANDED.value,
            min_cost=Money(3, 'USD'),
            max_cost=Money(4, 'USD'),
        )

        landed.delete()

        summary = StockItemCost.objects.get(stock_item=self.stock_item)
        self.assertEqual(summary.min_cost, Money(1, 'USD'))
        self.assertEqual(summary.max_cost, Money(2, 'USD'))

    def test_cascade_delete_with_stock_item(self):
        """Deleting the linked StockItem should also delete its cost summary."""
        StockItemCostEntry.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        pk = StockItemCost.objects.get(stock_item=self.stock_item).pk

        self.stock_item.delete()

        self.assertFalse(StockItemCost.objects.filter(pk=pk).exists())


class StockItemCostSummaryApiTest(PricingAPITestCase):
    """Tests for the (read-only) StockItemCost summary API endpoints."""

    @classmethod
    def setUpTestData(cls):
        """Initialize test data for the summary API tests."""
        super().setUpTestData()

        StockItemCostEntry.objects.create(
            stock_item=cls.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        cls.summary = StockItemCost.objects.get(stock_item=cls.stock_item)

    def test_retrieve(self):
        """Test that a StockItemCost summary can be retrieved by its own pk."""
        response = self.get(self.cost_detail_url(self.summary.pk))

        self.assertEqual(response.data['stock_item'], self.stock_item.pk)
        self.assertEqual(response.data['min_cost'], 1.0)
        self.assertEqual(response.data['max_cost'], 2.0)

    def test_list_and_filter(self):
        """Test listing and filtering StockItemCost summaries by stock item."""
        response = self.get(self.cost_list_url(), {'stock_item': self.stock_item.pk})
        self.assertEqual(len(response.data), 1)

        other_item = StockItem.objects.exclude(pk=self.stock_item.pk).first()
        response = self.get(self.cost_list_url(), {'stock_item': other_item.pk})
        self.assertEqual(len(response.data), 0)

    def test_read_only(self):
        """The summary endpoint should not accept create/update/delete requests."""
        self.post(
            self.cost_list_url(), {'stock_item': self.stock_item.pk}, expected_code=405
        )
        self.patch(self.cost_detail_url(self.summary.pk), {}, expected_code=405)
        self.delete(self.cost_detail_url(self.summary.pk), expected_code=405)

    def test_list_no_permission(self):
        """A user without 'pricing.view' permission cannot list cost summaries."""
        self.clearRoles()

        self.get(self.cost_list_url(), expected_code=403)
