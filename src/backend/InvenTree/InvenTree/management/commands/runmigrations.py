"""Check if there are any pending database migrations, and run them."""

from django.core.management.base import BaseCommand

import structlog

from InvenTree.tasks import check_for_migrations

logger = structlog.get_logger('inventree')


class Command(BaseCommand):
    """Check if there are any pending database migrations, and run them."""

    def handle(self, *args, **kwargs):
        """Check for any pending database migrations."""
        logger.info('Checking for pending database migrations')
        check_for_migrations(force=True, reload_registry=False)
        logger.info('Database migrations complete')
