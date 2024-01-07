"""Sample plugin for locating stock items / locations.

Note: This plugin does not *actually* locate anything!
"""

import logging

from plugin import InvenTreePlugin
from plugin.mixins import LocateMixin

logger = logging.getLogger('inventree')


class SampleLocatePlugin(LocateMixin, InvenTreePlugin):
    """A very simple example of the 'locate' plugin.

    This plugin class simply prints location information to the logger.
    """

    NAME = "SampleLocatePlugin"
    SLUG = "samplelocate"
    TITLE = "Sample plugin for locating items"

    VERSION = "0.2"

    def locate_stock_item(self, item_pk):
        """Locate a StockItem.

        Args:
            item_pk: primary key for item
        """
        from stock.models import StockItem

        logger.info("SampleLocatePlugin attempting to locate item ID %s", item_pk)

        try:
            item = StockItem.objects.get(pk=item_pk)
            logger.info("StockItem %s located!", item_pk)

            # Tag metadata
            item.set_metadata('located', True)

        except (ValueError, StockItem.DoesNotExist):  # pragma: no cover
            logger.exception("StockItem ID %s does not exist!", item_pk)

    def locate_stock_location(self, location_pk):
        """Locate a StockLocation.

        Args:
            location_pk: primary key for location
        """
        from stock.models import StockLocation

        logger.info(
            "SampleLocatePlugin attempting to locate location ID %s", location_pk
        )

        try:
            location = StockLocation.objects.get(pk=location_pk)
            logger.info("Location exists at '%s'", location.pathstring)

            # Tag metadata
            location.set_metadata('located', True)

        except (ValueError, StockLocation.DoesNotExist):  # pragma: no cover
            logger.exception("Location ID %s does not exist!", location_pk)
