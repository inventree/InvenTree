"""Unit tests for Part stale stock notification functionality."""

from datetime import timedelta
from unittest.mock import patch

from allauth.account.models import EmailAddress

import part.models
import part.tasks
import stock.models
from common.models import NotificationEntry, NotificationMessage
from common.settings import set_global_setting
from InvenTree import helpers
from InvenTree.unit_test import InvenTreeTestCase, addUserPermission


class StaleStockNotificationTests(InvenTreeTestCase):
    """Unit tests for stale stock notification functionality."""

    fixtures = ['category', 'part', 'location', 'stock']

    @classmethod
    def setUpTestData(cls):
        """Create test data as part of initialization."""
        super().setUpTestData()

        # Add email address for user
        EmailAddress.objects.create(user=cls.user, email='test@testing.com')

        # Create test parts
        cls.part1 = part.models.Part.objects.create(
            name='Test Part 1',
            description='A test part for stale stock testing',
            component=True,
        )

        cls.part2 = part.models.Part.objects.create(
            name='Test Part 2', description='Another test part', component=True
        )

        # Create test stock location
        cls.location = stock.models.StockLocation.objects.first()

    def setUp(self):
        """Setup routines."""
        super().setUp()

        # Enable stock expiry functionality
        set_global_setting('STOCK_ENABLE_EXPIRY', True, self.user)
        set_global_setting('STOCK_STALE_DAYS', 7, self.user)

        # Clear notifications
        NotificationEntry.objects.all().delete()  # type: ignore[attr-defined]
        NotificationMessage.objects.all().delete()  # type: ignore[attr-defined]

    def create_stock_items_with_expiry(self):
        """Create stock items with various expiry dates for testing."""
        today = helpers.current_date()

        # Create stock items with different expiry scenarios
        # Item 1: Expires tomorrow (stale)
        self.stock_item_stale = stock.models.StockItem.objects.create(
            part=self.part1,
            location=self.location,
            quantity=10,
            expiry_date=today + timedelta(days=1),
        )

        # Item 2: Already expired
        self.stock_item_expired = stock.models.StockItem.objects.create(
            part=self.part1,
            location=self.location,
            quantity=5,
            expiry_date=today - timedelta(days=1),
        )

        # Item 3: Expires in 2 weeks (not stale)
        self.stock_item_future = stock.models.StockItem.objects.create(
            part=self.part2,
            location=self.location,
            quantity=15,
            expiry_date=today + timedelta(days=14),
        )

        # Item 4: No expiry date
        self.stock_item_no_expiry = stock.models.StockItem.objects.create(
            part=self.part2, location=self.location, quantity=20
        )

        # Item 5: Out of stock but stale (should be ignored)
        self.stock_item_out_of_stock = stock.models.StockItem.objects.create(
            part=self.part1,
            location=self.location,
            quantity=0,
            expiry_date=today + timedelta(days=1),
        )

    def test_notify_stale_stock_with_empty_list(self):
        """Test notify_stale_stock with empty stale_items list."""
        # Should return early and do nothing
        part.tasks.notify_stale_stock(self.user, [])

        # No notifications should be created
        self.assertEqual(NotificationMessage.objects.count(), 0)  # type: ignore[attr-defined]

    def test_notify_stale_stock_single_item(self):
        """Test notify_stale_stock with a single stale item."""
        self.create_stock_items_with_expiry()

        # Mock the trigger_notification to verify it's called correctly
        with patch('common.notifications.trigger_notification') as mock_trigger:
            part.tasks.notify_stale_stock(self.user, [self.stock_item_stale])

            # Check that trigger_notification was called
            self.assertTrue(mock_trigger.called)
            _args, kwargs = mock_trigger.call_args

            # Check trigger object and category
            self.assertEqual(_args[0], self.stock_item_stale)
            self.assertEqual(_args[1], 'stock.notify_stale_stock')

            # Check context data
            context = kwargs['context']
            self.assertIn('1 stock item approaching', context['message'])

    def test_notify_stale_stock_multiple_items(self):
        """Test notify_stale_stock with multiple stale items."""
        self.create_stock_items_with_expiry()

        # Mock the trigger_notification to verify it's called correctly
        with patch('common.notifications.trigger_notification') as mock_trigger:
            # Call notify_stale_stock with multiple items
            stale_items = [self.stock_item_stale, self.stock_item_expired]
            part.tasks.notify_stale_stock(self.user, stale_items)

            # Check that trigger_notification was called
            self.assertTrue(mock_trigger.called)
            _args, kwargs = mock_trigger.call_args

            # Check context data
            context = kwargs['context']
            self.assertIn('2 stock items approaching', context['message'])

    def test_check_stale_stock_disabled_expiry(self):
        """Test check_stale_stock when stock expiry is disabled."""
        # Disable stock expiry
        set_global_setting('STOCK_ENABLE_EXPIRY', False, self.user)

        # Create stale stock items
        self.create_stock_items_with_expiry()

        # Call check_stale_stock
        with patch('part.tasks.logger') as mock_logger:
            part.tasks.check_stale_stock()
            mock_logger.info.assert_called_with(
                'Stock expiry functionality is not enabled - exiting'
            )

    def test_check_stale_stock_zero_stale_days(self):
        """Test check_stale_stock when STOCK_STALE_DAYS is 0."""
        # Set stale days to 0
        set_global_setting('STOCK_STALE_DAYS', 0, self.user)

        # Create stale stock items
        self.create_stock_items_with_expiry()

        # Call check_stale_stock
        with patch('part.tasks.logger') as mock_logger:
            part.tasks.check_stale_stock()
            mock_logger.info.assert_called_with(
                'Stock stale days is not configured or set to 0 - exiting'
            )

    def test_check_stale_stock_no_stale_items(self):
        """Test check_stale_stock when no stale items exist."""
        # Clear all existing stock items
        stock.models.StockItem.objects.update(parent=None)
        stock.models.StockItem.objects.all().delete()
        # Create only future expiry items
        today = helpers.current_date()
        stock.models.StockItem.objects.create(
            part=self.part1,
            location=self.location,
            quantity=10,
            expiry_date=today + timedelta(days=30),
        )

        # Call check_stale_stock
        with patch('part.tasks.logger') as mock_logger:
            part.tasks.check_stale_stock()
            mock_logger.info.assert_called_with('No stale stock items found')

    @patch('InvenTree.tasks.offload_task')
    def test_check_stale_stock_with_stale_items(self, mock_offload):
        """Test check_stale_stock when stale items exist."""
        # Clear existing stock items
        stock.models.StockItem.objects.update(parent=None)
        stock.models.StockItem.objects.all().delete()

        self.create_stock_items_with_expiry()

        # Subscribe user to parts
        addUserPermission(self.user, 'part', 'part', 'view')
        self.user.is_active = True
        self.user.save()
        self.part1.set_starred(self.user, True)

        # Call check_stale_stock
        with patch('part.tasks.logger') as mock_logger:
            part.tasks.check_stale_stock()

            # Check that stale items were found (stale and expired items)
            found_calls = []
            for call in mock_logger.info.call_args_list:
                call_str = str(call)
                if 'Found' in call_str and 'stale stock items' in call_str:
                    found_calls.append(call)
            self.assertGreater(len(found_calls), 0)

            # Check that notifications were scheduled
            scheduled_calls = []
            for call in mock_logger.info.call_args_list:
                if 'Scheduled stale stock notifications' in str(call):
                    scheduled_calls.append(call)
            self.assertGreater(len(scheduled_calls), 0)

            # Verify offload_task was called at least once
            self.assertTrue(mock_offload.called)

    def test_check_stale_stock_filtering(self):
        """Test that check_stale_stock properly filters stock items."""
        # Clear all existing stock items first
        stock.models.StockItem.objects.update(parent=None)
        stock.models.StockItem.objects.all().delete()

        today = helpers.current_date()

        # Create various stock items
        # Should be included: in stock + has expiry + within stale threshold
        _included_item = stock.models.StockItem.objects.create(
            part=self.part1,
            location=self.location,
            quantity=10,
            expiry_date=today + timedelta(days=3),  # Within 7-day threshold
        )

        # Should be excluded: no expiry date
        stock.models.StockItem.objects.create(
            part=self.part1, location=self.location, quantity=10
        )

        # Should be excluded: out of stock
        stock.models.StockItem.objects.create(
            part=self.part1,
            location=self.location,
            quantity=0,
            expiry_date=today + timedelta(days=3),
        )

        # Should be excluded: expiry too far in future
        stock.models.StockItem.objects.create(
            part=self.part1,
            location=self.location,
            quantity=10,
            expiry_date=today + timedelta(days=20),
        )

        # Call check_stale_stock and verify stale items were found
        with patch('InvenTree.tasks.offload_task') as _mock_offload:
            with patch('part.tasks.logger') as mock_logger:
                part.tasks.check_stale_stock()

                # Should find exactly 1 stale item
                mock_logger.info.assert_any_call('Found %s stale stock items', 1)
