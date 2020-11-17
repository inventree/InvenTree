""" Unit tests for Company views (see views.py) """

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import SupplierPart


class CompanyViewTestBase(TestCase):

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
        user = get_user_model()
        
        self.user = user.objects.create_user(
            username='username',
            email='user@email.com',
            password='password'
        )

        # Put the user into a group with the correct permissions
        group = Group.objects.create(name='mygroup')
        self.user.groups.add(group)

        # Give the group *all* the permissions!
        for rule in group.rule_sets.all():
            rule.can_view = True
            rule.can_change = True
            rule.can_add = True
            rule.can_delete = True

            rule.save()

        self.client.login(username='username', password='password')

    def post(self, url, data, valid=None):
        """
        POST against this form and return the response (as a JSON object)
        """

        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        # If a particular status code is required
        if valid is not None:
            if valid:
                self.assertEqual(json_data['form_valid'], True)
            else:
                self.assertEqual(json_data['form_valid'], False)

        form_errors = json.loads(json_data['form_errors'])

        return json_data, form_errors


class SupplierPartViewTests(CompanyViewTestBase):
    """
    Tests for the SupplierPart views.
    """

    def test_supplier_part_create(self):
        """
        Test the SupplierPartCreate view.
        
        This view allows some additional functionality,
        specifically it allows the user to create a single-quantity price break
        automatically, when saving the new SupplierPart model.
        """

        url = reverse('supplier-part-create')

        # First check that we can GET the form
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # How many supplier parts are already in the database?
        n = SupplierPart.objects.all().count()

        data = {
            'part': 1,
            'supplier': 1,
        }

        # SKU is required! (form should fail)
        (response, errors) = self.post(url, data, valid=False)

        self.assertIsNotNone(errors.get('SKU', None))

        data['SKU'] = 'TEST-ME-123'

        (response, errors) = self.post(url, data, valid=True)

        # Check that the SupplierPart was created!
        self.assertEqual(n + 1, SupplierPart.objects.all().count())

        # Check that it was created *without* a price-break
        supplier_part = SupplierPart.objects.get(pk=response['pk'])

        self.assertEqual(supplier_part.price_breaks.count(), 0)

        # Duplicate SKU is prohibited
        (response, errors) = self.post(url, data, valid=False)

        self.assertIsNotNone(errors.get('__all__', None))

        # Add with a different SKU, *and* a single-quantity price
        data['SKU'] = 'TEST-ME-1234'
        data['single_pricing_0'] = '123.4'
        data['single_pricing_1'] = 'CAD'

        (response, errors) = self.post(url, data, valid=True)

        pk = response.get('pk')

        # Check that *another* SupplierPart was created
        self.assertEqual(n + 2, SupplierPart.objects.all().count())

        supplier_part = SupplierPart.objects.get(pk=pk)

        # Check that a price-break has been created!
        self.assertEqual(supplier_part.price_breaks.count(), 1)

        price_break = supplier_part.price_breaks.first()

        self.assertEqual(price_break.quantity, 1)

    def test_supplier_part_delete(self):
        """
        Test the SupplierPartDelete view
        """

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


class CompanyViewTest(CompanyViewTestBase):
    """
    Tests for various 'Company' views
    """

    def test_company_index(self):
        """ Test the company index """

        response = self.client.get(reverse('company-index'))
        self.assertEqual(response.status_code, 200)

    def test_company_create(self):
        """
        Test the view for creating a company
        """

        # Check that different company types return different form titles
        response = self.client.get(reverse('supplier-create'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 'Create new Supplier')

        response = self.client.get(reverse('manufacturer-create'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 'Create new Manufacturer')

        response = self.client.get(reverse('customer-create'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 'Create new Customer')
