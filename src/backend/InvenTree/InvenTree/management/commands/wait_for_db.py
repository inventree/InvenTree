"""Custom management command, wait for the database to be ready!"""

import time

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to pause execution until the database is ready."""

    def handle(self, *args, **kwargs):
        """Wait till the database is ready."""
        self.stdout.write('Waiting for database...')

        connected = False

        while not connected:
            time.sleep(2)

            try:
                connection.ensure_connection()

                connected = True

            except OperationalError as e:
                self.stdout.write(f'Could not connect to database: {e}')
            except ImproperlyConfigured as e:
                self.stdout.write(f'Improperly configured: {e}')
            else:
                if not connection.is_usable():
                    self.stdout.write('Database configuration is not usable')

            if connected:
                self.stdout.write('Database connection successful!')
