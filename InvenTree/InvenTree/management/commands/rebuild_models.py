"""Custom management command to rebuild all MPTT models.

- This is crucial after importing any fixtures, etc
"""

import logging

from django.core.management.base import BaseCommand

from maintenance_mode.core import maintenance_mode_on, set_maintenance_mode

logger = logging.getLogger('inventree')


class Command(BaseCommand):
    """Rebuild all database models which leverage the MPTT structure."""

    def handle(self, *args, **kwargs):
        """Rebuild all database models which leverage the MPTT structure."""
        with maintenance_mode_on():
            self.rebuild_models()

        set_maintenance_mode(False)

    def rebuild_models(self):
        """Rebuild all MPTT models in the database."""
        # Part model
        try:
            logger.info('Rebuilding Part objects')

            from part.models import Part

            Part.objects.rebuild()
        except Exception:
            logger.info('Error rebuilding Part objects')

        # Part category
        try:
            logger.info('Rebuilding PartCategory objects')

            from part.models import PartCategory

            PartCategory.objects.rebuild()
        except Exception:
            logger.info('Error rebuilding PartCategory objects')

        # StockItem model
        try:
            logger.info('Rebuilding StockItem objects')

            from stock.models import StockItem

            StockItem.objects.rebuild()
        except Exception:
            logger.info('Error rebuilding StockItem objects')

        # StockLocation model
        try:
            logger.info('Rebuilding StockLocation objects')

            from stock.models import StockLocation

            StockLocation.objects.rebuild()
        except Exception:
            logger.info('Error rebuilding StockLocation objects')

        # Build model
        try:
            logger.info('Rebuilding Build objects')

            from build.models import Build

            Build.objects.rebuild()
        except Exception:
            logger.info('Error rebuilding Build objects')
