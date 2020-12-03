""" Unit tests for Stock views (see views.py) """

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

import json

from common.models import InvenTreeSetting
from InvenTree.status_codes import StockStatus


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
        # Test creation of StockItem
        response = self.client.get(reverse('stock-item-create'), {'part': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('stock-item-create'), {'part': 999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Copy from a valid item, valid location
        response = self.client.get(reverse('stock-item-create'), {'location': 1, 'copy': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # Copy from an invalid item, invalid location
        response = self.client.get(reverse('stock-item-create'), {'location': 999, 'copy': 9999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

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


class StockOwnershipTest(StockViewTestCase):
    """ Tests for stock ownership views """

    def setUp(self):
        """ Add another user for ownership tests """

        super().setUp()

        # Promote existing user with staff, admin and superuser statuses
        self.user.is_staff = True
        self.user.is_admin = True
        self.user.is_superuser = True
        self.user.save()

        # Create a new user
        user = get_user_model()
        
        self.new_user = user.objects.create_user(
            username='john',
            email='john@email.com',
            password='custom123',
        )

        # Put the user into a new group with the correct permissions
        group = Group.objects.create(name='new_group')
        self.new_user.groups.add(group)

        # Give the group *all* the permissions!
        for rule in group.rule_sets.all():
            rule.can_view = True
            rule.can_change = True
            rule.can_add = True
            rule.can_delete = True

            rule.save()

    def enable_ownership(self):
        # Enable stock location ownership

        InvenTreeSetting.set_setting('STOCK_OWNERSHIP_CONTROL', True, self.user)
        self.assertEqual(True, InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL'))

    def test_owner_control(self):
        # Test stock location and item ownership
        from .models import StockLocation, StockItem

        user_group = self.user.groups.all()[0]
        new_user_group = self.new_user.groups.all()[0]

        test_location_id = 4
        test_item_id = 11

        # Enable ownership control
        self.enable_ownership()

        # Set ownership on existing location
        response = self.client.post(reverse('stock-location-edit', args=(test_location_id,)),
                                    {'name': 'Office', 'owner': user_group.pk},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, '"form_valid": true', status_code=200)

        # Set ownership on existing item (change location to pk=4)
        response = self.client.post(reverse('stock-item-edit', args=(test_item_id,)),
                                    {'part': 1, 'status': StockStatus.OK, 'owner': self.user.pk},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, '"form_valid": true', status_code=200)

        # Create new location
        # new_location = {
        #     'name': 'Desk',
        #     'parent': test_location_id,
        #     'description': 'My office desk',
        # }

        # response = self.client.post(reverse('stock-location-create'),
        #                             new_location, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        # # print(response.content)
        # self.assertContains(response, '"form_valid": true', status_code=200)
        
        # # Make sure the new location's owner is same as its parent
        # parent_location = StockLocation.objects.get(pk=test_location_id)
        # print(f'\n{parent_location.owner=}\n')
        # # new_location = StockLocation.objects.get(pk=new_location_id)

        # # Create new item
        # new_item = {
        #     'part': 25,
        #     'location': 0,
        # }

        # Logout
        self.client.logout()

        # Login with new user
        self.client.login(username='john', password='custom123')

        # Test location edit
        response = self.client.post(reverse('stock-location-edit', args=(test_location_id,)),
                                    {'name': 'Office', 'owner': new_user_group.pk},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        # Make sure the location's owner is unchanged
        location = StockLocation.objects.get(pk=test_location_id)
        self.assertEqual(location.owner, user_group)

        # Test item edit
        response = self.client.post(reverse('stock-item-edit', args=(test_item_id,)),
                                    {'part': 1, 'status': StockStatus.OK, 'owner': self.new_user.pk},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, '"form_valid": false', status_code=200)

        # Make sure the item's owner is unchanged
        item = StockItem.objects.get(pk=test_item_id)
        self.assertEqual(item.owner, self.user)
