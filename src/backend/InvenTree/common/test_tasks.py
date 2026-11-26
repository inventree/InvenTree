"""Tests for tasks in app common."""

from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

import requests

from common.models import NewsFeedEntry, NotificationEntry
from common.settings import set_global_setting
from InvenTree.tasks import offload_task

from . import tasks as common_tasks


class TaskTest(TestCase):
    """Tests for common tasks."""

    def test_delete_old_notifications(self):
        """Test that old notification entries are deleted according to the setting.

        Previously, a second task in common.tasks deleted entries after a
        hard-coded 90 days, silently capping INVENTREE_DELETE_NOTIFICATIONS_DAYS.
        """
        from InvenTree.tasks import delete_old_notifications

        # The duplicate task has been removed
        self.assertFalse(hasattr(common_tasks, 'delete_old_notifications'))

        # Empty run
        self.assertEqual(NotificationEntry.objects.all().count(), 0)
        offload_task(delete_old_notifications)

        now = timezone.now()

        for key, age in [('recent', 10), ('medium', 100), ('old', 200)]:
            NotificationEntry.objects.create(key=key, uid=1)
            NotificationEntry.objects.filter(key=key).update(
                updated=now - timedelta(days=age)
            )

        # Retention period longer than 90 days is respected
        set_global_setting('INVENTREE_DELETE_NOTIFICATIONS_DAYS', 150)
        offload_task(delete_old_notifications)

        self.assertEqual(
            set(NotificationEntry.objects.values_list('key', flat=True)),
            {'recent', 'medium'},
        )

        # Shorter retention period
        set_global_setting('INVENTREE_DELETE_NOTIFICATIONS_DAYS', 30)
        offload_task(delete_old_notifications)

        self.assertEqual(
            list(NotificationEntry.objects.values_list('key', flat=True)), ['recent']
        )


class NewsFeedTests(TestCase):
    """Tests for update_news_feed task.

    Tests cover different networking and addressing possibilities.
    """

    def setUp(self):
        """Setup for tests."""
        # Needs to be set to allow SQLite to store entries
        settings.USE_TZ = True

        # Store setting to restore on teardown
        self.news_url = settings.INVENTREE_NEWS_URL

        NewsFeedEntry.objects.all().delete()

    def tearDown(self):
        """Teardown for tests."""
        # Restore proper setting
        settings.INVENTREE_NEWS_URL = self.news_url

        NewsFeedEntry.objects.all().delete()

    def test_valid_url(self):
        """Tests that news feed is updated when accessing a valid URL."""
        try:
            common_tasks.update_news_feed()
        except Exception as ex:  # pragma: no cover
            self.fail(f'News feed raised exceptions: {ex}')

        self.assertNotEqual(NewsFeedEntry.objects.all().count(), 0)

    def test_connection_error(self):
        """Test connecting to an unavailable endpoint.

        This also emulates calling the endpoint behind a blocking proxy.
        """
        settings.INVENTREE_NEWS_URL = 'http://10.255.255.1:81'

        # Simulate the connection timing out, rather than waiting for a real timeout
        with (
            patch(
                'common.tasks.requests.get',
                side_effect=requests.exceptions.ConnectTimeout,
            ) as mock_get,
            self.assertLogs('inventree', level='WARNING'),
        ):
            common_tasks.update_news_feed()

        mock_get.assert_called_once_with(settings.INVENTREE_NEWS_URL, timeout=30)

        self.assertEqual(NewsFeedEntry.objects.all().count(), 0)

    def test_unset_url(self):
        """Test that no call is made to news feed if URL setting is invalid."""
        settings.INVENTREE_NEWS_URL = ''

        self.assertTrue(
            offload_task(common_tasks.update_news_feed)
        )  # Task considered complete
        self.assertEqual(
            NewsFeedEntry.objects.all().count(), 0
        )  # No Feed entries created

        settings.INVENTREE_NEWS_URL = 0

        self.assertTrue(
            offload_task(common_tasks.update_news_feed)
        )  # Task considered complete
        self.assertEqual(
            NewsFeedEntry.objects.all().count(), 0
        )  # No Feed entries created

        settings.INVENTREE_NEWS_URL = None

        self.assertTrue(
            offload_task(common_tasks.update_news_feed)
        )  # Task considered complete
        self.assertEqual(
            NewsFeedEntry.objects.all().count(), 0
        )  # No Feed entries created
