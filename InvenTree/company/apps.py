from __future__ import unicode_literals

import os
import logging

from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError
from django.conf import settings


logger = logging.getLogger(__name__)


class CompanyConfig(AppConfig):
    name = 'company'

    def ready(self):
        """
        This function is called whenever the Company app is loaded.
        """

        self.generate_company_thumbs()

    def generate_company_thumbs(self):

        from .models import Company

        logger.debug("Checking Company image thumbnails")

        try:
            for company in Company.objects.all():
                if company.image:
                    url = company.image.thumbnail.name
                    loc = os.path.join(settings.MEDIA_ROOT, url)

                    if not os.path.exists(loc):
                        logger.info("InvenTree: Generating thumbnail for Company '{c}'".format(c=company.name))
                        try:
                            company.image.render_variations(replace=False)
                        except FileNotFoundError:
                            logger.warning("Image file missing")
                            company.image = None
                            company.save()
        except (OperationalError, ProgrammingError):
            # Getting here probably meant the database was in test mode
            pass
