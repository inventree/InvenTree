"""
Unit testing for BOM export functionality
"""

from django.test import TestCase

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class BomExportTest(TestCase):

    fixtures = [
        'category',
        'part',
        'location',
        'bom',
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

        self.url = reverse('bom-download', kwargs={'pk': 100})

    def test_export_csv(self):
        """
        Test BOM download in CSV format
        """

        print("URL", self.url)

        params = {
            'file_format': 'csv',
            'cascade': True,
            'parameter_data': True,
            'stock_data': True,
            'supplier_data': True,
            'manufacturer_data': True,
        }

        response = self.client.get(self.url, data=params)

        self.assertEqual(response.status_code, 200)

        content = response.headers['Content-Disposition']
        self.assertEqual(content, 'attachment; filename="BOB | Bob | A2_BOM.csv"')

    def test_export_xls(self):
        """
        Test BOM download in XLS format
        """

        params = {
            'file_format': 'xls',
            'cascade': True,
            'parameter_data': True,
            'stock_data': True,
            'supplier_data': True,
            'manufacturer_data': True,
        }

        response = self.client.get(self.url, data=params)

        self.assertEqual(response.status_code, 200)

        content = response.headers['Content-Disposition']
        self.assertEqual(content, 'attachment; filename="BOB | Bob | A2_BOM.xls"')

    def test_export_xlsx(self):
        """
        Test BOM download in XLSX format
        """

        params = {
            'file_format': 'xlsx',
            'cascade': True,
            'parameter_data': True,
            'stock_data': True,
            'supplier_data': True,
            'manufacturer_data': True,
        }

        response = self.client.get(self.url, data=params)

        self.assertEqual(response.status_code, 200)

    def test_export_json(self):
        """
        Test BOM download in JSON format
        """

        params = {
            'file_format': 'json',
            'cascade': True,
            'parameter_data': True,
            'stock_data': True,
            'supplier_data': True,
            'manufacturer_data': True,
        }

        response = self.client.get(self.url, data=params)

        self.assertEqual(response.status_code, 200)

        content = response.headers['Content-Disposition']
        self.assertEqual(content, 'attachment; filename="BOB | Bob | A2_BOM.json"')
