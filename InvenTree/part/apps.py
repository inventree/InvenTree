from __future__ import unicode_literals

import os
import logging

from django.db.utils import OperationalError, ProgrammingError
from django.apps import AppConfig
from django.conf import settings

from PIL import UnidentifiedImageError

from InvenTree.ready import canAppAccessDatabase


logger = logging.getLogger("inventree")


class PartConfig(AppConfig):
    name = 'part'

    def ready(self):
        """
        This function is called whenever the Part app is loaded.
        """

        if canAppAccessDatabase():
            self.update_trackable_status()

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
