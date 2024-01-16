"""Custom management command to rebuild thumbnail images.

- May be required after importing a new dataset, for example
"""

import logging
import os

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

        # Check for image paths
        img_paths = []

        if model.image and model.image.path:
            img_paths.append(model.image.path)

        if model.image.thumbnail and model.image.thumbnail.path:
            img_paths.append(model.image.thumbnail.path)

        if model.image.preview and model.image.preview.path:
            img_paths.append(model.image.preview.path)

        if len(img_paths) > 0:
            if all((os.path.exists(path) for path in img_paths)):
                # All images exist - skip further work
                return

        logger.info("Generating thumbnail image for '%s'", img)

        try:
            model.image.render_variations(replace=False)
        except FileNotFoundError:
            logger.warning("Warning: Image file '%s' is missing", img)
        except UnidentifiedImageError:
            logger.warning("Warning: Image file '%s' is not a valid image", img)

    def handle(self, *args, **kwargs):
        """Rebuild all thumbnail images."""
        logger.info('Rebuilding Part thumbnails')

        for part in Part.objects.exclude(image=None):
            try:
                self.rebuild_thumbnail(part)
            except (OperationalError, ProgrammingError):
                logger.exception('ERROR: Database read error.')
                break

        logger.info('Rebuilding Company thumbnails')

        for company in Company.objects.exclude(image=None):
            try:
                self.rebuild_thumbnail(company)
            except (OperationalError, ProgrammingError):
                logger.exception('ERROR: abase read error.')
                break
