""" Unit tests for Order views (see views.py) """

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from InvenTree.status_codes import OrderStatus

from .models import PurchaseOrder, PurchaseOrderLineItem

import json


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

    def test_po_issue(self):
        """ Test PurchaseOrderIssue view """

        url = reverse('purchase-order-issue', args=(1,))

        order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(order.status, OrderStatus.PENDING)

        # Test without confirmation
        response = self.client.post(url, {'confirm': 0}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertFalse(data['form_valid'])

        # Test WITH confirmation
        response = self.client.post(url, {'confirm': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['form_valid'])

        # Test that the order was actually placed
        order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(order.status, OrderStatus.PLACED)

    def test_line_item_create(self):
        """ Test the form for adding a new LineItem to a PurchaseOrder """

        # Record the number of line items in the PurchaseOrder
        po = PurchaseOrder.objects.get(pk=1)
        n = po.lines.count()
        self.assertEqual(po.status, OrderStatus.PENDING)

        url = reverse('po-line-item-create')

        # GET the form (pass the correct info)
        response = self.client.get(url, {'order': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        post_data = {
            'part': 100,
            'quantity': 45,
            'reference': 'Test reference field',
            'notes': 'Test notes field'
        }

        # POST with an invalid purchase order
        post_data['order'] = 99
        response = self.client.post(url, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content)
        self.assertFalse(data['form_valid'])
        self.assertIn('Invalid Purchase Order', str(data['html_form']))

        # POST with a part that does not match the purchase order
        post_data['order'] = 1
        post_data['part'] = 7
        response = self.client.post(url, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content)
        self.assertFalse(data['form_valid'])
        self.assertIn('must match for Part and Order', str(data['html_form']))

        # POST with an invalid part
        post_data['part'] = 12345
        response = self.client.post(url, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content)
        self.assertFalse(data['form_valid'])
        self.assertIn('Invalid SupplierPart selection', str(data['html_form']))

        # POST the form with valid data
        post_data['part'] = 100
        response = self.client.post(url, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['form_valid'])

        self.assertEqual(n + 1, PurchaseOrder.objects.get(pk=1).lines.count())

        line = PurchaseOrderLineItem.objects.get(order=1, part=100)
        self.assertEqual(line.quantity, 45)

    def test_line_item_edit(self):
        """ Test editing form for PO line item """

        url = reverse('po-line-item-edit', args=(22,))

        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)


class TestPOReceive(OrderViewTestCase):
    """ Tests for receiving a purchase order """

    def setUp(self):
        super().setUp()

        self.po = PurchaseOrder.objects.get(pk=1)
        self.url = reverse('purchase-order-receive', args=(1,))

    def test_receive_lines(self):
        
        # TODO
        pass
