"""
Unit testing for BOM export functionality
"""

import csv

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse


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

    def test_bom_template(self):
        """
        Test that the BOM template can be downloaded from the server
        """

        url = reverse('bom-upload-template')

        # Download an XLS template
        response = self.client.get(url, data={'format': 'xls'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers['Content-Disposition'],
            'attachment; filename="InvenTree_BOM_Template.xls"'
        )

        # Return a simple CSV template
        response = self.client.get(url, data={'format': 'csv'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers['Content-Disposition'],
            'attachment; filename="InvenTree_BOM_Template.csv"'
        )

        filename = '_tmp.csv'

        with open(filename, 'wb') as f:
            f.write(response.getvalue())

        with open(filename, 'r') as f:
            reader = csv.reader(f, delimiter=',')

            for line in reader:
                headers = line
                break

            expected = [
                'part_id',
                'part_ipn',
                'part_name',
                'quantity',
                'optional',
                'overage',
                'reference',
                'note',
                'inherited',
                'allow_variants',
            ]

            # Ensure all the expected headers are in the provided file
            for header in expected:
                self.assertTrue(header in headers)

    def test_export_csv(self):
        """
        Test BOM download in CSV format
        """

        params = {
            'format': 'csv',
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

        filename = '_tmp.csv'

        with open(filename, 'wb') as f:
            f.write(response.getvalue())

        # Read the file
        with open(filename, 'r') as f:
            reader = csv.reader(f, delimiter=',')

            for line in reader:
                headers = line
                break

            expected = [
                'level',
                'bom_id',
                'parent_part_id',
                'parent_part_ipn',
                'parent_part_name',
                'part_id',
                'part_ipn',
                'part_name',
                'part_description',
                'sub_assembly',
                'quantity',
                'optional',
                'overage',
                'reference',
                'note',
                'inherited',
                'allow_variants',
                'Default Location',
                'Total Stock',
                'Available Stock',
                'On Order',
            ]

            for header in expected:
                self.assertTrue(header in headers)

            for header in headers:
                self.assertTrue(header in expected)

    def test_export_xls(self):
        """
        Test BOM download in XLS format
        """

        params = {
            'format': 'xls',
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
            'format': 'xlsx',
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
            'format': 'json',
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
