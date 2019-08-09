""" Unit tests for Order views (see views.py) """

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class OrderViewTestCase(TestCase):
    
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

    def setUp(self):
        super().setUp()

        # Create a user
        User = get_user_model()
        User.objects.create_user('username', 'user@email.com', 'password')

        self.client.login(username='username', password='password')


class OrderListTest(OrderViewTestCase):

    def test_order_list(self):
        response = self.client.get(reverse('purchase-order-index'))

        self.assertEqual(response.status_code, 200)


class POTests(OrderViewTestCase):
    """ Tests for PurchaseOrder views """

    def test_detail_view(self):
        """ Retrieve PO detail view """
        response = self.client.get(reverse('purchase-order-detail', args=(1,)))
        self.assertEqual(response.status_code, 200)
        keys = response.context.keys()
        self.assertIn('OrderStatus', keys)

    def test_po_create(self):
        """ Launch forms to create new PurchaseOrder"""
        url = reverse('purchase-order-create')

        # Without a supplier ID
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # With a valid supplier ID
        response = self.client.get(url, {'supplier': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # With an invalid supplier ID
        response = self.client.get(url, {'supplier': 'goat'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_po_edit(self):
        """ Launch form to edit a PurchaseOrder """

        response = self.client.get(reverse('purchase-order-edit', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_po_export(self):
        """ Export PurchaseOrder """

        response = self.client.get(reverse('purchase-order-export', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Response should be streaming-content (file download)
        self.assertIn('streaming_content', dir(response))
