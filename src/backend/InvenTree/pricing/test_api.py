"""Unit tests for the pricing API."""

from django.urls import reverse

from djmoney.money import Money

from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from stock.models import StockItem

from .models import StockItemCost
from .status_codes import CostType


class PricingAPITestCase(InvenTreeAPITestCase):
    """Base class for pricing API tests."""

    fixtures = ['category', 'part', 'location', 'stock']

    roles = ['pricing.view', 'pricing.add', 'pricing.delete']

    @classmethod
    def setUpTestData(cls):
        """Initialize test data for the pricing API tests."""
        super().setUpTestData()

        cls.part = Part.objects.get(pk=1)
        cls.stock_item = StockItem.objects.get(pk=1)

    def list_url(self):
        """Return the URL for the StockItemCost list endpoint."""
        return reverse('api-pricing-cost-list')

    def detail_url(self, pk):
        """Return the URL for a specific StockItemCost detail endpoint."""
        return reverse('api-pricing-cost-detail', kwargs={'pk': pk})

    def status_url(self):
        """Return the URL for the CostType status code endpoint."""
        return reverse('api-pricing-cost-status-codes')


class StockItemCostListTest(PricingAPITestCase):
    """Tests for listing and creating StockItemCost entries."""

    def test_list_empty(self):
        """An empty list should be returned if no cost entries exist."""
        response = self.get(self.list_url())
        self.assertEqual(response.data, [])

    def test_create(self):
        """Test creation of a new StockItemCost entry via the API."""
        data = {
            'stock_item': self.stock_item.pk,
            'cost_type': CostType.PURCHASE.value,
            'min_cost': '1.500',
            'min_cost_currency': 'USD',
            'max_cost': '2.500',
            'max_cost_currency': 'USD',
            'notes': 'Some notes',
        }

        response = self.post(self.list_url(), data)

        cost = StockItemCost.objects.get(pk=response.data['pk'])

        # The 'part' field should be automatically populated from the stock item
        self.assertEqual(cost.part, self.stock_item.part)

        # The 'user' field should be automatically populated from the request
        self.assertEqual(cost.user, self.user)

        self.assertEqual(cost.cost_type, CostType.PURCHASE.value)
        self.assertEqual(cost.min_cost, Money('1.5', 'USD'))
        self.assertEqual(cost.max_cost, Money('2.5', 'USD'))
        self.assertEqual(cost.notes, 'Some notes')

    def test_create_no_permission(self):
        """A user without 'pricing.add' permission cannot create a cost entry."""
        self.clearRoles()
        self.assignRole('pricing.view')

        data = {'stock_item': self.stock_item.pk, 'cost_type': CostType.PURCHASE.value}

        self.post(self.list_url(), data, expected_code=403)

    def test_list_no_permission(self):
        """A user without 'pricing.view' permission cannot list cost entries."""
        self.clearRoles()

        self.get(self.list_url(), expected_code=403)

    def test_list_and_filter(self):
        """Test listing and filtering of StockItemCost entries."""
        other_item = StockItem.objects.exclude(part=self.stock_item.part).first()

        StockItemCost.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(1, 'USD'),
            max_cost=Money(2, 'USD'),
        )

        StockItemCost.objects.create(
            stock_item=self.stock_item,
            cost_type=CostType.LANDED.value,
            min_cost=Money(3, 'USD'),
            max_cost=Money(4, 'USD'),
        )

        StockItemCost.objects.create(
            stock_item=other_item,
            cost_type=CostType.PURCHASE.value,
            min_cost=Money(5, 'USD'),
            max_cost=Money(6, 'USD'),
        )

        # Filter by linked stock item
        response = self.get(self.list_url(), {'stock_item': self.stock_item.pk})
        self.assertEqual(len(response.data), 2)

        # Filter by linked part (denormalized field)
        response = self.get(self.list_url(), {'part': self.stock_item.part.pk})
        self.assertEqual(len(response.data), 2)

        # Filter by cost type
        response = self.get(self.list_url(), {'cost_type': CostType.LANDED.value})
        self.assertEqual(len(response.data), 1)

        # No filters - expect all three entries
        response = self.get(self.list_url())
        self.assertEqual(len(response.data), 3)


class StockItemCostDetailTest(PricingAPITestCase):
    """Tests for retrieving and deleting individual StockItemCost entries."""

    @classmethod
    def setUpTestData(cls):
        """Initialize test data for the pricing API detail tests."""
        super().setUpTestData()

        cls.cost = StockItemCost.objects.create(
            stock_item=cls.stock_item,
            cost_type=CostType.MANUAL.value,
            min_cost=Money(10, 'USD'),
            max_cost=Money(20, 'USD'),
            notes='Test cost entry',
        )

    def test_retrieve(self):
        """Test that a single StockItemCost entry can be retrieved."""
        response = self.get(self.detail_url(self.cost.pk))

        self.assertEqual(response.data['pk'], self.cost.pk)
        self.assertEqual(response.data['stock_item'], self.stock_item.pk)
        self.assertEqual(response.data['part'], self.stock_item.part.pk)
        self.assertEqual(response.data['notes'], 'Test cost entry')

    def test_retrieve_optional_fields(self):
        """Test that optional detail fields can be requested."""
        self.run_output_test(
            self.detail_url(self.cost.pk),
            ['part_detail', 'stock_item_detail', 'user_detail'],
        )

    def test_update_not_allowed(self):
        """StockItemCost entries are part of an append-only ledger, and cannot be updated.

        Note: Grant 'change' permission here, to prove that PUT/PATCH are rejected
        because no update endpoint exists - not merely due to a permission failure.
        """
        self.assignRole('pricing.change')

        self.patch(
            self.detail_url(self.cost.pk), {'notes': 'Updated'}, expected_code=405
        )
        self.put(self.detail_url(self.cost.pk), {'notes': 'Updated'}, expected_code=405)

    def test_delete(self):
        """Test that a StockItemCost entry can be deleted."""
        self.delete(self.detail_url(self.cost.pk))
        self.assertFalse(StockItemCost.objects.filter(pk=self.cost.pk).exists())

    def test_delete_no_permission(self):
        """A user without 'pricing.delete' permission cannot delete a cost entry."""
        self.clearRoles()
        self.assignRole('pricing.view')

        self.delete(self.detail_url(self.cost.pk), expected_code=403)

    def test_cascade_delete_with_stock_item(self):
        """Deleting the linked StockItem should also delete any associated cost entries."""
        pk = self.cost.pk

        self.stock_item.delete()

        self.assertFalse(StockItemCost.objects.filter(pk=pk).exists())


class StockItemCostStatusTest(PricingAPITestCase):
    """Tests for the CostType status code endpoint."""

    def test_status_codes(self):
        """Test that the CostType status codes are correctly reported."""
        response = self.get(self.status_url())

        self.assertEqual(response.data['status_class'], 'CostType')

        values = response.data['values']

        for name in ['PURCHASE', 'LANDED', 'MANUFACTURING', 'MANUAL', 'SYSTEM']:
            self.assertIn(name, values)
