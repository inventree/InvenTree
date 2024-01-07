"""part app specification"""

import logging

from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

from InvenTree.ready import (
    canAppAccessDatabase,
    isImportingData,
    isInMainThread,
    isPluginRegistryLoaded,
)

logger = logging.getLogger('inventree')


class PartConfig(AppConfig):
    """Config class for the 'part' app"""

    name = 'part'

    def ready(self):
        """This function is called whenever the Part app is loaded."""
        # skip loading if plugin registry is not loaded or we run in a background thread
        if not isPluginRegistryLoaded() or not isInMainThread():
            return

        if canAppAccessDatabase():
            self.update_trackable_status()
            self.reset_part_pricing_flags()

    def update_trackable_status(self):
        """Check for any instances where a trackable part is used in the BOM for a non-trackable part.

        In such a case, force the top-level part to be trackable too.
        """
        from .models import BomItem

        try:
            items = BomItem.objects.filter(
                part__trackable=False, sub_part__trackable=True
            )

            for item in items:
                logger.info("Marking part '%s' as trackable", item.part.name)
                item.part.trackable = True
                item.part.clean()
                item.part.save()
        except (OperationalError, ProgrammingError):  # pragma: no cover
            # Exception if the database has not been migrated yet
            pass

    def reset_part_pricing_flags(self):
        """Performed on startup, to ensure that all pricing objects are in a "good" state.

        Prevents issues with state machine if the server is restarted mid-update
        """
        from .models import PartPricing

        if isImportingData():
            return

        try:
            items = PartPricing.objects.filter(scheduled_for_update=True)

            if items.count() > 0:
                # Find any pricing objects which have the 'scheduled_for_update' flag set
                logger.info(
                    'Resetting update flags for %s pricing objects...', items.count()
                )

                for pricing in items:
                    pricing.scheduled_for_update = False
                    pricing.save()
        except Exception:
            logger.exception('Failed to reset pricing flags - database not ready')
