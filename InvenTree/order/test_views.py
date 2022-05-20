""" Unit tests for Order views (see views.py) """

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse


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
        user = get_user_model().objects.create_user('username', 'user@email.com', 'password')

        # Ensure that the user has the correct permissions!
        g = Group.objects.create(name='orders')
        user.groups.add(g)

        for rule in g.rule_sets.all():
            if rule.name in ['purchase_order', 'sales_order']:
                rule.can_change = True
                rule.can_add = True
                rule.can_delete = True

                rule.save()

        g.save()

        self.client.login(username='username', password='password')


class OrderListTest(OrderViewTestCase):

    def test_order_list(self):
        response = self.client.get(reverse('po-index'))

        self.assertEqual(response.status_code, 200)


class PurchaseOrderTests(OrderViewTestCase):
    """ Tests for PurchaseOrder views """

    def test_detail_view(self):
        """ Retrieve PO detail view """
        response = self.client.get(reverse('po-detail', args=(1,)))
        self.assertEqual(response.status_code, 200)
        keys = response.context.keys()
        self.assertIn('PurchaseOrderStatus', keys)

    def test_po_export(self):
        """ Export PurchaseOrder """

        response = self.client.get(reverse('po-export', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Response should be streaming-content (file download)
        self.assertIn('streaming_content', dir(response))
