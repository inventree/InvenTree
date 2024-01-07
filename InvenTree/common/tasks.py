"""Tasks (processes that get offloaded) for common app."""

import logging
import os
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import AppRegistryNotReady
from django.db.utils import IntegrityError, OperationalError
from django.utils import timezone

import feedparser

from InvenTree.helpers_model import getModelsWithMixin
from InvenTree.models import InvenTreeNotesMixin
from InvenTree.tasks import ScheduledTask, scheduled_task

logger = logging.getLogger('inventree')


@scheduled_task(ScheduledTask.DAILY)
def delete_old_notifications():
    """Remove old notifications from the database.

    Anything older than ~3 months is removed
    """
    try:
        from common.models import NotificationEntry
    except AppRegistryNotReady:  # pragma: no cover
        logger.info(
            "Could not perform 'delete_old_notifications' - App registry not ready"
        )
        return

    before = timezone.now() - timedelta(days=90)

    # Delete notification records before the specified date
    NotificationEntry.objects.filter(updated__lte=before).delete()


@scheduled_task(ScheduledTask.DAILY)
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
        logger.warning('update_news_feed: Error parsing the newsfeed', entry)
        return

    # Get a reference list
    id_list = [a.feed_id for a in NewsFeedEntry.objects.all()]

    # Iterate over entries
    for entry in d.entries:
        # Check if id already exists
        if entry.id in id_list:
            continue

        # Create entry
        try:
            NewsFeedEntry.objects.create(
                feed_id=entry.id,
                title=entry.title,
                link=entry.link,
                published=entry.published,
                author=entry.author,
                summary=entry.summary,
            )
        except (IntegrityError, OperationalError):
            # Sometimes errors-out on database start-up
            pass

    logger.info('update_news_feed: Sync done')


@scheduled_task(ScheduledTask.DAILY)
def delete_old_notes_images():
    """Remove old notes images from the database.

    Anything older than ~3 months is removed, unless it is linked to a note
    """
    try:
        from common.models import NotesImage
    except AppRegistryNotReady:
        logger.info(
            "Could not perform 'delete_old_notes_images' - App registry not ready"
        )
        return

    # Remove any notes which point to non-existent image files
    for note in NotesImage.objects.all():
        if not os.path.exists(note.image.path):
            logger.info('Deleting note %s - image file does not exist', note.image.path)
            note.delete()

    note_classes = getModelsWithMixin(InvenTreeNotesMixin)
    before = datetime.now() - timedelta(days=90)

    for note in NotesImage.objects.filter(date__lte=before):
        # Find any images which are no longer referenced by a note

        found = False

        img = note.image.name

        for model in note_classes:
            if model.objects.filter(notes__icontains=img).exists():
                found = True
                break

        if not found:
            logger.info('Deleting note %s - image file not linked to a note', img)
            note.delete()

    # Finally, remove any images in the notes dir which are not linked to a note
    notes_dir = os.path.join(settings.MEDIA_ROOT, 'notes')

    try:
        images = os.listdir(notes_dir)
    except FileNotFoundError:
        # Thrown if the directory does not exist
        images = []

    all_notes = NotesImage.objects.all()

    for image in images:
        found = False
        for note in all_notes:
            img_path = os.path.basename(note.image.path)
            if img_path == image:
                found = True
                break

        if not found:
            logger.info('Deleting note %s - image file not linked to a note', image)
            os.remove(os.path.join(notes_dir, image))
