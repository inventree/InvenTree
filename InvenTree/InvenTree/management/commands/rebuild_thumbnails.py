"""Custom management command to rebuild thumbnail images.

- May be required after importing a new dataset, for example
"""

import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError, ProgrammingError

from PIL import UnidentifiedImageError

from company.models import Company
from part.models import Part

logger = logging.getLogger('inventree')


class Command(BaseCommand):
    """Rebuild all thumbnail images."""

    def rebuild_thumbnail(self, model):
        """Rebuild the thumbnail specified by the "image" field of the provided model."""
        if not model.image:
            return

        img = model.image
        url = img.thumbnail.name
        loc = os.path.join(settings.MEDIA_ROOT, url)

        if not os.path.exists(loc):
            logger.info(f"Generating thumbnail image for '{img}'")

            try:
                model.image.render_variations(replace=False)
            except FileNotFoundError:
                logger.warning(f"Warning: Image file '{img}' is missing")
            except UnidentifiedImageError:
                logger.warning(f"Warning: Image file '{img}' is not a valid image")

    def handle(self, *args, **kwargs):

        logger.info("Rebuilding Part thumbnails")

        for part in Part.objects.exclude(image=None):
            try:
                self.rebuild_thumbnail(part)
            except (OperationalError, ProgrammingError):
                logger.error("ERROR: Database read error.")
                break

        logger.info("Rebuilding Company thumbnails")

        for company in Company.objects.exclude(image=None):
            try:
                self.rebuild_thumbnail(company)
            except (OperationalError, ProgrammingError):
                logger.error("ERROR: abase read error.")
                break
