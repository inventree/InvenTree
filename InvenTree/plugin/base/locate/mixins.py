"""Plugin mixin for locating stock items and locations"""

import logging

from plugin.helpers import MixinNotImplementedError

logger = logging.getLogger('inventree')


class LocateMixin:
    """
    Mixin class which provides support for 'locating' inventory items,
    for example identifying the location of a particular StockLocation.

    Plugins could implement audible or visual cues to direct attention to the location,
    with (for e.g.) LED strips or buzzers, or some other method.

    The plugins may also be used to *deliver* a particular stock item to the user.

    A class which implements this mixin may implement the following methods:

    - locate_stock_item : Used to locate / identify a particular stock item
    - locate_stock_location : Used to locate / identify a particular stock location

    Refer to the default method implementations below for more information!

    """

    class MixinMeta:
        MIXIN_NAME = "Locate"

    def __init__(self):
        super().__init__()
        self.add_mixin('locate', True, __class__)

    def locate_stock_item(self, item_pk):
        """
        Attempt to locate a particular StockItem

        Arguments:
            item_pk: The PK (primary key) of the StockItem to be located

        The default implementation for locating a StockItem
        attempts to locate the StockLocation where the item is located.

        An attempt is only made if the StockItem is *in stock*

        Note: A custom implemenation could always change this behaviour
        """

        logger.info(f"LocateMixin: Attempting to locate StockItem pk={item_pk}")

        from stock.models import StockItem

        try:
            item = StockItem.objects.get(pk=item_pk)

            if item.in_stock and item.location is not None:
                self.locate_stock_location(item.location.pk)

        except StockItem.DoesNotExist:
            logger.warning("LocateMixin: StockItem pk={item_pk} not found")
            pass

    def locate_stock_location(self, location_pk):
        """
        Attempt to location a particular StockLocation

        Arguments:
            location_pk: The PK (primary key) of the StockLocation to be located

        Note: The default implementation here does nothing!
        """
        raise MixinNotImplementedError
