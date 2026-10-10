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
        connected = False
        verbose = int(kwargs.get('verbosity', 0)) > 0
        attempts = kwargs.get('attempts', 10)

        if verbose:
            self.stdout.write('Waiting for database connection...')
            self.stdout.flush()

        while not connected and attempts > 0:
            attempts -= 1

            try:
                connection.ensure_connection()

                connected = True

            except (OperationalError, ImproperlyConfigured):
                if verbose:
                    self.stdout.write('Database connection failed, retrying ...')
                    self.stdout.flush()
            else:
                if not connection.is_usable():
                    if verbose:
                        self.stdout.write('Database configuration is not usable')
                        self.stdout.flush()

            if connected:
                if verbose:
                    self.stdout.write('Database connection successful!')
                    self.stdout.flush()
            else:
                time.sleep(1)

        if not connected:
            self.stderr.write('Failed to connect to database after multiple attempts')
            self.stderr.flush()
