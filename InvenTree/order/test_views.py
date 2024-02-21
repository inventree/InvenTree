"""Unit tests for Order views (see views.py)."""

from django.conf.locale import ta
from django.test import tag
from django.urls import reverse

from InvenTree.unit_test import InvenTreeTestCase


class OrderViewTestCase(InvenTreeTestCase):
    """Base unit test class for order views."""

    fixtures = [
        'category',
        'part',
        'bom',
        'location',
        'company',
        'supplier_part',
        'stock',
        'order',
        'sales_order',
        'return_order',
    ]

    roles = [
        'purchase_order.change',
        'purchase_order.add',
        'purchase_order.delete',
        'sales_order.change',
        'sales_order.add',
        'sales_order.delete',
        'return_order.change',
        'return_order.add',
        'return_order.delete',
    ]


@tag('cui')
class PurchaseOrderListTest(OrderViewTestCase):
    """Unit tests for the PurchaseOrder index page."""

    def test_order_list(self):
        """Tests for the PurchaseOrder index page."""
        response = self.client.get(reverse('purchase-order-index'))

        self.assertEqual(response.status_code, 200)


@tag('cui')
class PurchaseOrderTests(OrderViewTestCase):
    """Tests for PurchaseOrder views."""

    def test_detail_view(self):
        """Retrieve PO detail view."""
        response = self.client.get(reverse('po-detail', args=(1,)))
        self.assertEqual(response.status_code, 200)
        keys = response.context.keys()
        self.assertIn('PurchaseOrderStatus', keys)

    def test_po_export(self):
        """Export PurchaseOrder."""
        response = self.client.get(
            reverse('po-export', args=(1,)),
            headers={'x-requested-with': 'XMLHttpRequest'},
        )

        # Response should be streaming-content (file download)
        self.assertIn('streaming_content', dir(response))


@tag('cui')
class SalesOrderViews(OrderViewTestCase):
    """Unit tests for the SalesOrder pages."""

    def test_index(self):
        """Test the SalesOrder index page."""
        response = self.client.get(reverse('sales-order-index'))
        self.assertEqual(response.status_code, 200)

    def test_detail(self):
        """Test SalesOrder detail view."""
        response = self.client.get(reverse('so-detail', args=(1,)))
        self.assertEqual(response.status_code, 200)


@tag('cui')
class ReturnOrderVIews(OrderViewTestCase):
    """Unit tests for the ReturnOrder pages."""

    def test_index(self):
        """Test the ReturnOrder index page."""
        response = self.client.get(reverse('return-order-index'))
        self.assertEqual(response.status_code, 200)

    def test_detail(self):
        """Test ReturnOrder detail view."""
        response = self.client.get(reverse('return-order-detail', args=(1,)))
        self.assertEqual(response.status_code, 200)
