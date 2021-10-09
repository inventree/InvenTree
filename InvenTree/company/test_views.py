""" Unit tests for Company views (see views.py) """

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class CompanyViewTestBase(TestCase):

    fixtures = [
        'category',
        'part',
        'location',
        'company',
        'manufacturer_part',
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


class CompanyViewTest(CompanyViewTestBase):
    """
    Tests for various 'Company' views
    """

    def test_company_index(self):
        """ Test the company index """

        response = self.client.get(reverse('company-index'))
        self.assertEqual(response.status_code, 200)
