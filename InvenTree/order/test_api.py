"""
Tests for the Order API
"""

from datetime import datetime, timedelta

from rest_framework.test import APITestCase
from rest_framework import status

from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import PurchaseOrder, SalesOrder


class OrderTest(APITestCase):

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'supplier_part',
        'stock',
        'order',
        'sales_order',
    ]

    def setUp(self):

        # Create a user for auth
        get_user_model().objects.create_user('testuser', 'test@testing.com', 'password')
        self.client.login(username='testuser', password='password')

    def doGet(self, url, data={}):

        return self.client.get(url, data=data, format='json')

    def doPost(self, url, data={}):
        return self.client.post(url, data=data, format='json')

    def filter(self, filters, count):
        """
        Test API filters
        """

        response = self.doGet(
            self.LIST_URL,
            filters
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), count)

        return response


class PurchaseOrderTest(OrderTest):
    """
    Tests for the PurchaseOrder API
    """

    LIST_URL = reverse('api-po-list')

    def test_po_list(self):

        # List *ALL* PO items
        self.filter({}, 6)

        # Filter by supplier
        self.filter({'supplier': 1}, 1)
        self.filter({'supplier': 3}, 5)

        # Filter by "outstanding"
        self.filter({'outstanding': True}, 4)
        self.filter({'outstanding': False}, 2)

        # Filter by "status"
        self.filter({'status': 10}, 2)
        self.filter({'status': 40}, 1)

    def test_overdue(self):
        """
        Test "overdue" status
        """

        self.filter({'overdue': True}, 0)
        self.filter({'overdue': False}, 6)

        order = PurchaseOrder.objects.get(pk=1)
        order.target_date = datetime.now().date() - timedelta(days=10)
        order.save()

        self.filter({'overdue': True}, 1)
        self.filter({'overdue': False}, 5)

    def test_po_detail(self):

        url = '/api/order/po/1/'

        response = self.doGet(url)
        
        self.assertEqual(response.status_code, 200)

        data = response.data

        self.assertEqual(data['pk'], 1)
        self.assertEqual(data['description'], 'Ordering some screws')

    def test_po_attachments(self):

        url = reverse('api-po-attachment-list')

        response = self.doGet(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
    

class SalesOrderTest(OrderTest):
    """
    Tests for the SalesOrder API
    """

    LIST_URL = reverse('api-so-list')

    def test_so_list(self):

        # All orders
        self.filter({}, 5)

        # Filter by customer
        self.filter({'customer': 4}, 3)
        self.filter({'customer': 5}, 2)

        # Filter by outstanding
        self.filter({'outstanding': True}, 3)
        self.filter({'outstanding': False}, 2)

        # Filter by status
        self.filter({'status': 10}, 3)  # PENDING
        self.filter({'status': 20}, 1)  # SHIPPED
        self.filter({'status': 99}, 0)  # Invalid

    def test_overdue(self):
        """
        Test "overdue" status
        """

        self.filter({'overdue': True}, 0)
        self.filter({'overdue': False}, 5)

        for pk in [1, 2]:
            order = SalesOrder.objects.get(pk=pk)
            order.target_date = datetime.now().date() - timedelta(days=10)
            order.save()

        self.filter({'overdue': True}, 2)
        self.filter({'overdue': False}, 3)

    def test_so_detail(self):

        url = '/api/order/so/1/'

        response = self.doGet(url)

        self.assertEqual(response.status_code, 200)

        data = response.data

        self.assertEqual(data['pk'], 1)

    def test_so_attachments(self):

        url = reverse('api-so-attachment-list')

        response = self.doGet(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
