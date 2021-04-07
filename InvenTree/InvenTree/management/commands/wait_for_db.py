"""
Custom management command, wait for the database to be ready!
"""

from django.core.management.base import BaseCommand

from django.db import connections
from django.db.utils import OperationalError

from part.models import Part

import time


class Command(BaseCommand):
    """
    django command to pause execution until the database is ready
    """

    def handle(self, *args, **kwargs):
        self.stdout.write("Waiting for database...")

        db_conn = None

        while not db_conn:
            try:
                # get the database with keyword 'default' from settings.py
                db_conn = connections['default']

                # Try to read some data from the database
                Part.objects.count()

                # prints success messge in green
                self.stdout.write(self.style.SUCCESS('InvenTree database connected'))
            except:
                self.stdout.write(self.style.ERROR("Database unavailable, waiting 5 seconds ..."))
                time.sleep(5)
