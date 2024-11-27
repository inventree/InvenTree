"""Event definitions and triggers for the stock app."""

from generic.events import BaseEventEnum


class StockEvents(BaseEventEnum):
    """Event enumeration for the Stock app."""

    # StockItem events
    ITEM_ASSIGNED_TO_CUSTOMER = 'stockitem.assignedtocustomer'
    ITEM_RETURNED_FROM_CUSTOMER = 'stockitem.returnedfromcustomer'
    ITEM_SPLIT = 'stockitem.split'
    ITEM_MOVED = 'stockitem.moved'
    ITEM_COUNTED = 'stockitem.counted'
    ITEM_QUANTITY_UPDATED = 'stockitem.quantityupdated'
    ITEM_INSTALLED_INTO_ASSEMBLY = 'stockitem.installed'
