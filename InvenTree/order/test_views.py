"""Unit tests for Order views (see views.py)"""

from django.urls import reverse

from InvenTree.helpers import InvenTreeTestCase


class OrderViewTestCase(InvenTreeTestCase):
    """Base unit test class for order views"""
    fixtures = [
        'category',
        'part',
        'bom',
        'location',
        'company',
        'supplier_part',
        'stock',
        'order',
    ]

    roles = [
        'purchase_order.change',
        'purchase_order.add',
        'purchase_order.delete',
        'sales_order.change',
        'sales_order.add',
        'sales_order.delete',
    ]


class PurchaseOrderTests(OrderViewTestCase):
    """Tests for PurchaseOrder views."""

    def test_po_export(self):
        """Export PurchaseOrder."""
        response = self.client.get(reverse('po-export', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Response should be streaming-content (file download)
        self.assertIn('streaming_content', dir(response))
