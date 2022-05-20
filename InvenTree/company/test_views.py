""" Unit tests for Company views (see views.py) """

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse


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


class CompanyViewTest(CompanyViewTestBase):
    """
    Tests for various 'Company' views
    """

    def test_company_index(self):
        """ Test the company index """

        response = self.client.get(reverse('company-index'))
        self.assertEqual(response.status_code, 200)

    def test_manufacturer_index(self):
        """ Test the manufacturer index """

        response = self.client.get(reverse('manufacturer-index'))
        self.assertEqual(response.status_code, 200)

    def test_customer_index(self):
        """ Test the customer index """

        response = self.client.get(reverse('customer-index'))
        self.assertEqual(response.status_code, 200)

    def test_manufacturer_part_detail_view(self):
        """ Test the manufacturer part detail view """

        response = self.client.get(reverse('manufacturer-part-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MPN123')

    def test_supplier_part_detail_view(self):
        """ Test the supplier part detail view """

        response = self.client.get(reverse('supplier-part-detail', kwargs={'pk': 10}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MPN456-APPEL')
