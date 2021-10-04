from __future__ import unicode_literals

import os
import logging

from PIL import UnidentifiedImageError

from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError
from django.conf import settings

from InvenTree.ready import canAppAccessDatabase


logger = logging.getLogger("inventree")


class CompanyConfig(AppConfig):
    name = 'company'

    def ready(self):
        """
        This function is called whenever the Company app is loaded.
        """

        pass
