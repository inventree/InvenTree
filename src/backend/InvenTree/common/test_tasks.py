"""Tests for tasks in app common."""

from django.conf import settings
from django.test import TestCase

from common.models import NewsFeedEntry, NotificationEntry
from InvenTree.tasks import offload_task

from . import tasks as common_tasks


class TaskTest(TestCase):
    """Tests for common tasks."""

    def test_delete(self):
        """Test that the task `delete_old_notifications` runs through without errors."""
        # check empty run
        self.assertEqual(NotificationEntry.objects.all().count(), 0)
        offload_task(common_tasks.delete_old_notifications)


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
        except Exception as ex:
            self.fail(f'News feed raised exceptions: {ex}')

        self.assertNotEqual(NewsFeedEntry.objects.all().count(), 0)

    def test_connection_error(self):
        """Test connecting to an unavailable endpoint.

        This also emulates calling the endpoint behind a blocking proxy.
        """
        settings.INVENTREE_NEWS_URL = 'http://10.255.255.1:81'

        with self.assertLogs('inventree', level='WARNING'):
            common_tasks.update_news_feed()

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
