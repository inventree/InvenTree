"""
Custom management command, wait for the database to be ready!
"""

from django.core.management.base import BaseCommand

from django.db import connections
from django.db.utils import OperationalError

import psycopg2

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
                # prints success messge in green
                self.stdout.write(self.style.SUCCESS('InvenTree database connected'))
            except (OperationalError, psycopg2.OperationalError):
                self.stdout.write(self.style.ERROR("Database unavailable, waiting 5 seconds ..."))
                time.sleep(5)
