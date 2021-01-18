# Tests for labels

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.test import APITestCase

from django.urls import reverse
from django.contrib.auth import get_user_model


class TestReportTests(APITestCase):
    """
    Tests for the StockItem TestReport templates
    """

    fixtures = [
        'category',
        'part',
        'location',
        'stock',
    ]

    list_url = reverse('api-stockitem-testreport-list')

    def setUp(self):
        user = get_user_model()

        self.user = user.objects.create_user('testuser', 'test@testing.com', 'password')

        self.user.is_staff = True
        self.user.save()

        self.client.login(username='testuser', password='password')

    def do_list(self, filters={}):

        response = self.client.get(self.list_url, filters, format='json')

        self.assertEqual(response.status_code, 200)

        return response.data

    def test_list(self):
        
        response = self.do_list()

        # TODO - Add some report templates to the fixtures
        self.assertEqual(len(response), 0)

        # TODO - Add some tests to this response
        response = self.do_list(
            {
                'item': 10,
            }
        )

        # TODO - Add some tests to this response
        response = self.do_list(
            {
                'item': 100000,
            }
        )

        # TODO - Add some tests to this response
        response = self.do_list(
            {
                'items': [10, 11, 12],
            }
        )
