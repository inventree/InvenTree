"""Unit tests for Order views (see views.py)."""

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
