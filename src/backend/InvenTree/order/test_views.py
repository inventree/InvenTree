"""Unit tests for Order views (see views.py)."""

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
class PurchaseOrderTests(OrderViewTestCase):
    """Tests for PurchaseOrder views."""

    def test_po_export(self):
        """Export PurchaseOrder."""
        response = self.client.get(
            reverse('po-export', args=(1,)),
            headers={'x-requested-with': 'XMLHttpRequest'},
        )

        # Response should be streaming-content (file download)
        self.assertIn('streaming_content', dir(response))
