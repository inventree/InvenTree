""" Unit tests for Company views (see views.py) """

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import SupplierPart


class CompanyViewTest(TestCase):

    fixtures = [
        'category',
        'part',
        'location',
        'company',
        'supplier_part',
    ]

    def setUp(self):
        super().setUp()

        # Create a user
        User = get_user_model()
        User.objects.create_user('username', 'user@email.com', 'password')

        self.client.login(username='username', password='password')

    def test_company_index(self):
        """ Test the company index """

        response = self.client.get(reverse('company-index'))
        self.assertEqual(response.status_code, 200)

    def test_supplier_part_delete(self):
        """ Test the SupplierPartDelete view """

        url = reverse('supplier-part-delete')

        # Get form using 'part' argument
        response = self.client.get(url, {'part': '1'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Get form using 'parts' argument
        response = self.client.get(url + '?parts[]=1&parts[]=2', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # POST to delete two parts
        n = SupplierPart.objects.count()
        response = self.client.post(
            url,
            {
                'supplier-part-2': 'supplier-part-2',
                'supplier-part-3': 'supplier-part-3',
                'confirm_delete': True
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)

        self.assertEqual(n - 2, SupplierPart.objects.count())
