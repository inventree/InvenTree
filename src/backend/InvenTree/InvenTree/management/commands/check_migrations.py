"""Check if there are any pending database migrations, and run them."""

import logging

from django.core.management.base import BaseCommand

from InvenTree.tasks import check_for_migrations

logger = logging.getLogger('inventree')


class Command(BaseCommand):
    """Check if there are any pending database migrations, and run them."""

    def handle(self, *args, **kwargs):
        """Check for any pending database migrations."""
        logger.info('Checking for pending database migrations')
        check_for_migrations(force=True, reload_registry=False)
        logger.info('Database migrations complete')
