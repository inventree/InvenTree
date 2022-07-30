"""Tasks (processes that get offloaded) for common app."""

import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import AppRegistryNotReady

import feedparser

logger = logging.getLogger('inventree')


def delete_old_notifications():
    """Remove old notifications from the database.

    Anything older than ~3 months is removed
    """
    try:
        from common.models import NotificationEntry
    except AppRegistryNotReady:  # pragma: no cover
        logger.info("Could not perform 'delete_old_notifications' - App registry not ready")
        return

    before = datetime.now() - timedelta(days=90)

    # Delete notification records before the specified date
    NotificationEntry.objects.filter(updated__lte=before).delete()


def update_news_feed():
    """Update the newsfeed."""
    try:
        from common.models import NewsFeedEntry
    except AppRegistryNotReady:  # pragma: no cover
        logger.info("Could not perform 'update_news_feed' - App registry not ready")
        return

    # Fetch and parse feed
    try:
        d = feedparser.parse(settings.INVENTREE_NEWS_URL)
    except Exception as entry:  # pragma: no cover
        logger.warning("update_news_feed: Error parsing the newsfeed", entry)
        return

    # Get a reference list
    id_list = [a.feed_id for a in NewsFeedEntry.objects.all()]

    # Iterate over entries
    for entry in d.entries:
        # Check if id already exsists
        if entry.id in id_list:
            continue

        # Create entry
        NewsFeedEntry.objects.create(
            feed_id=entry.id,
            title=entry.title,
            link=entry.link,
            published=entry.published,
            author=entry.author,
            summary=entry.summary,
        )

    logger.info('update_news_feed: Sync done')
