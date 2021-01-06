""" Unit tests for Stock views (see views.py) """

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from common.models import InvenTreeSetting

import json
from datetime import datetime, timedelta


class StockViewTestCase(TestCase):

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'supplier_part',
        'stock',
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

        self.user.is_staff = True
        self.user.save()

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


class StockListTest(StockViewTestCase):
    """ Tests for Stock list views """

    def test_stock_index(self):
        response = self.client.get(reverse('stock-index'))
        self.assertEqual(response.status_code, 200)


class StockLocationTest(StockViewTestCase):
    """ Tests for StockLocation views """

    def test_location_edit(self):
        response = self.client.get(reverse('stock-location-edit', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_qr_code(self):
        # Request the StockLocation QR view
        response = self.client.get(reverse('stock-location-qr', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Test for an invalid StockLocation
        response = self.client.get(reverse('stock-location-qr', args=(999,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_create(self):
        # Test StockLocation creation view
        response = self.client.get(reverse('stock-location-create'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Create with a parent
        response = self.client.get(reverse('stock-location-create'), {'location': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Create with an invalid parent
        response = self.client.get(reverse('stock-location-create'), {'location': 999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        

class StockItemTest(StockViewTestCase):
    """" Tests for StockItem views """

    def test_qr_code(self):
        # QR code for a valid item
        response = self.client.get(reverse('stock-item-qr', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # QR code for an invalid item
        response = self.client.get(reverse('stock-item-qr', args=(9999,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        data = str(response.content)
        self.assertIn('Error:', data)

    def test_adjust_items(self):
        url = reverse('stock-adjust')

        # Move items
        response = self.client.get(url, {'stock[]': [1, 2, 3, 4, 5], 'action': 'move'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Count part
        response = self.client.get(url, {'part': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Remove items
        response = self.client.get(url, {'location': 1, 'action': 'take'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Add items
        response = self.client.get(url, {'item': 1, 'action': 'add'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Blank response
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # TODO - Tests for POST data

    def test_edit_item(self):
        # Test edit view for StockItem
        response = self.client.get(reverse('stock-item-edit', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Test with a non-purchaseable part
        response = self.client.get(reverse('stock-item-edit', args=(100,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_create_item(self):
        """
        Test creation of StockItem
        """

        url = reverse('stock-item-create')

        response = self.client.get(url, {'part': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url, {'part': 999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Copy from a valid item, valid location
        response = self.client.get(url, {'location': 1, 'copy': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Copy from an invalid item, invalid location
        response = self.client.get(url, {'location': 999, 'copy': 9999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_create_stock_with_expiry(self):
        """
        Test creation of stock item of a part with an expiry date.
        The initial value for the "expiry_date" field should be pre-filled,
        and should be in the future!
        """

        # First, ensure that the expiry date feature is enabled!
        InvenTreeSetting.set_setting('STOCK_ENABLE_EXPIRY', True, self.user)

        url = reverse('stock-item-create')

        response = self.client.get(url, {'part': 25}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)

        # We are expecting 10 days in the future
        expiry = datetime.now().date() + timedelta(10)

        expected = f'name=\\\\"expiry_date\\\\" value=\\\\"{expiry.isoformat()}\\\\"'

        self.assertIn(expected, str(response.content))

        # Now check with a part which does *not* have a default expiry period
        response = self.client.get(url, {'part': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        expected = 'name=\\\\"expiry_date\\\\" placeholder=\\\\"\\\\"'

        self.assertIn(expected, str(response.content))

    def test_serialize_item(self):
        # Test the serialization view

        url = reverse('stock-item-serialize', args=(100,))

        # GET the form
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        data_valid = {
            'quantity': 5,
            'serial_numbers': '1-5',
            'destination': 4,
            'notes': 'Serializing stock test'
        }

        data_invalid = {
            'quantity': 4,
            'serial_numbers': 'dd-23-adf',
            'destination': 'blorg'
        }
        
        # POST
        response = self.client.post(url, data_valid, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['form_valid'])

        # Try again to serialize with the same numbers
        response = self.client.post(url, data_valid, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['form_valid'])

        # POST with invalid data
        response = self.client.post(url, data_invalid, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['form_valid'])
