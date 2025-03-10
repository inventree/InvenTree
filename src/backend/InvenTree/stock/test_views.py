"""Unit tests for Stock views (see views.py)."""

from django.contrib.auth.models import Group
from django.urls import reverse

from common.models import InvenTreeSetting
from InvenTree.unit_test import InvenTreeTestCase
from stock.models import StockItem, StockLocation
from stock.status_codes import StockStatus
from users.models import Owner


class StockViewTestCase(InvenTreeTestCase):
    """Mixin for Stockview tests."""

    fixtures = ['category', 'part', 'company', 'location', 'supplier_part', 'stock']

    roles = 'all'


class StockOwnershipTest(StockViewTestCase):
    """Tests for stock ownership views."""

    test_item_id = 11
    test_location_id = 1

    def enable_ownership(self):
        """Helper function to turn on ownership control."""
        # Enable stock location ownership

        InvenTreeSetting.set_setting('STOCK_OWNERSHIP_CONTROL', True, self.user)
        self.assertEqual(True, InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL'))

    def assert_ownership(self, assertion: bool = True, user=None):
        """Helper function to check ownership control."""
        if user is None:
            user = self.user

        item = StockItem.objects.get(pk=self.test_item_id)
        self.assertEqual(assertion, item.check_ownership(user))

        location = StockLocation.objects.get(pk=self.test_location_id)
        self.assertEqual(assertion, location.check_ownership(user))

    def assert_api_change(self):
        """Helper function to get response to API change."""
        return self.client.patch(
            reverse('api-stock-detail', args=(self.test_item_id,)),
            {'status': StockStatus.DAMAGED.value},
            content_type='application/json',
        )

    def test_owner_no_ownership(self):
        """Check without ownership control enabled. Should always return True."""
        self.assert_ownership(True)

    def test_ownership_as_superuser(self):
        """Test that superuser are always allowed to access items."""
        self.enable_ownership()

        # Check with superuser
        self.user.is_superuser = True
        self.user.save()
        self.assert_ownership(True)

    def test_ownership_functions(self):
        """Test that ownership is working correctly for StockItem/StockLocation."""
        self.enable_ownership()
        item = StockItem.objects.get(pk=self.test_item_id)
        location = StockLocation.objects.get(pk=self.test_location_id)

        # Check that user is not allowed to change item
        self.assertTrue(item.check_ownership(self.user))  # No owner -> True
        self.assertTrue(location.check_ownership(self.user))  # No owner -> True
        self.assertContains(
            self.assert_api_change(),
            'You do not have permission to perform this action.',
            status_code=403,
        )

        # Adjust group rules
        group = Group.objects.get(name='my_test_group')
        rule = group.rule_sets.get(name='stock')
        rule.can_change = True
        rule.save()

        # Set owner to group of user
        group_owner = Owner.get_owner(group)
        item.owner = group_owner
        item.save()
        location.owner = group_owner
        location.save()

        # Check that user is allowed to change item
        self.assertTrue(item.check_ownership(self.user))  # Owner is group -> True
        self.assertTrue(location.check_ownership(self.user))  # Owner is group -> True
        self.assertContains(
            self.assert_api_change(),
            f'"status":{StockStatus.DAMAGED.value}',
            status_code=200,
        )

        # Change group
        new_group = Group.objects.create(name='new_group')
        new_group_owner = Owner.get_owner(new_group)
        item.owner = new_group_owner
        item.save()
        location.owner = new_group_owner
        location.save()

        # Check that user is not allowed to change item
        self.assertFalse(
            item.check_ownership(self.user)
        )  # Owner is not in group -> False
        self.assertFalse(
            location.check_ownership(self.user)
        )  # Owner is not in group -> False
