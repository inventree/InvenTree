from __future__ import unicode_literals

import os

from django.db.utils import OperationalError, ProgrammingError
from django.apps import AppConfig
from django.conf import settings


class PartConfig(AppConfig):
    name = 'part'

    def ready(self):
        """
        This function is called whenever the Part app is loaded.
        """

        self.generate_part_thumbnails()

    def generate_part_thumbnails(self):
        from .models import Part

        print("InvenTree: Checking Part image thumbnails")

        try:
            for part in Part.objects.all():
                if part.image:
                    url = part.image.thumbnail.name
                    loc = os.path.join(settings.MEDIA_ROOT, url)
                    
                    if not os.path.exists(loc):
                        print("InvenTree: Generating thumbnail for Part '{p}'".format(p=part.name))
                        try:
                            part.image.render_variations(replace=False)
                        except FileNotFoundError:
                            print("Image file missing")
                            part.image = None
                            part.save()
        except (OperationalError, ProgrammingError):
            print("Could not generate Part thumbnails")
