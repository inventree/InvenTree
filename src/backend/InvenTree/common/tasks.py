"""Tasks (processes that get offloaded) for common app."""

import os
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import AppRegistryNotReady
from django.db.utils import IntegrityError, OperationalError
from django.utils import timezone

import feedparser
import requests
import structlog
from opentelemetry import trace

import common.models
import InvenTree.helpers
from InvenTree.helpers_model import getModelsWithMixin
from InvenTree.models import InvenTreeNotesMixin
from InvenTree.tasks import ScheduledTask, scheduled_task

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger('inventree')


@tracer.start_as_current_span('cleanup_old_data_outputs')
@scheduled_task(ScheduledTask.DAILY)
def cleanup_old_data_outputs():
    """Remove old data outputs from the database."""
    # Remove any outputs which are older than 5 days
    # Note: Remove them individually, to ensure that the files are removed too
    threshold = InvenTree.helpers.current_date() - timedelta(days=5)

    for output in common.models.DataOutput.objects.filter(created__lte=threshold):
        output.delete()


@tracer.start_as_current_span('delete_old_notifications')
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


@tracer.start_as_current_span('update_news_feed')
@scheduled_task(ScheduledTask.DAILY)
def update_news_feed():
    """Update the newsfeed."""
    try:
        from common.models import NewsFeedEntry
    except AppRegistryNotReady:  # pragma: no cover
        logger.info("Could not perform 'update_news_feed' - App registry not ready")
        return

    # News feed isn't defined, no need to continue
    if not settings.INVENTREE_NEWS_URL or not isinstance(
        settings.INVENTREE_NEWS_URL, str
    ):
        return

    # Fetch and parse feed
    try:
        feed = requests.get(settings.INVENTREE_NEWS_URL, timeout=30)
        d = feedparser.parse(feed.content)
    except Exception:  # pragma: no cover
        logger.warning('update_news_feed: Error parsing the newsfeed')
        return

    # Get a reference list
    id_list = [a.feed_id for a in NewsFeedEntry.objects.all()]

    # Iterate over entries
    for entry in d.entries:
        # Check if id already exists
        if entry.id in id_list:
            continue

        # Enforce proper links for the entries
        if entry.link and str(entry.link).startswith('/'):
            entry.link = settings.INVENTREE_BASE_URL + str(entry.link)

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


@tracer.start_as_current_span('delete_old_notes_images')
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
    before = InvenTree.helpers.current_date() - timedelta(days=90)

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


@tracer.start_as_current_span('rebuild_parameters')
def rebuild_parameters(template_id):
    """Rebuild all parameters for a given template.

    This function is called when a base template is changed,
    which may cause the base unit to be adjusted.
    """
    from common.models import Parameter, ParameterTemplate

    try:
        template = ParameterTemplate.objects.get(pk=template_id)
    except ParameterTemplate.DoesNotExist:
        return

    parameters = Parameter.objects.filter(template=template)

    n = 0

    for parameter in parameters:
        # Update the parameter if the numeric value has changed
        value_old = parameter.data_numeric
        parameter.calculate_numeric_value()

        if value_old != parameter.data_numeric:
            parameter.full_clean()
            parameter.save()
            n += 1

    if n > 0:
        logger.info("Rebuilt %s parameters for template '%s'", n, template.name)
