from __future__ import unicode_literals

import os
import logging

from django.db.utils import OperationalError, ProgrammingError
from django.apps import AppConfig
from django.conf import settings


logger = logging.getLogger(__name__)


class PartConfig(AppConfig):
    name = 'part'

    def ready(self):
        """
        This function is called whenever the Part app is loaded.
        """

        self.generate_part_thumbnails()
        self.update_trackable_status()

    def generate_part_thumbnails(self):
        """
        Generate thumbnail images for any Part that does not have one.
        This function exists mainly for legacy support,
        as any *new* image uploaded will have a thumbnail generated automatically.
        """

        from .models import Part

        logger.debug("InvenTree: Checking Part image thumbnails")

        try:
            for part in Part.objects.all():
                if part.image:
                    url = part.image.thumbnail.name
                    loc = os.path.join(settings.MEDIA_ROOT, url)
                    
                    if not os.path.exists(loc):
                        logger.info("InvenTree: Generating thumbnail for Part '{p}'".format(p=part.name))
                        try:
                            part.image.render_variations(replace=False)
                        except FileNotFoundError:
                            logger.warning("Image file missing")
                            part.image = None
                            part.save()
        except (OperationalError, ProgrammingError):
            # Exception if the database has not been migrated yet
            pass

    def update_trackable_status(self):
        """
        Check for any instances where a trackable part is used in the BOM
        for a non-trackable part.

        In such a case, force the top-level part to be trackable too.
        """

        from .models import BomItem

        try:
            items = BomItem.objects.filter(part__trackable=False, sub_part__trackable=True)

            for item in items:
                print(f"Marking part '{item.part.name}' as trackable")
                item.part.trackable = True
                item.part.clean()
                item.part.save()
        except (OperationalError, ProgrammingError):
            # Exception if the database has not been migrated yet
            pass
