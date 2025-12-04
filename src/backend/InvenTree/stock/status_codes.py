"""Stock status codes."""

from django.utils.translation import gettext_lazy as _

from generic.states import ColorEnum, StatusCode


class StockStatus(StatusCode):
    """Status codes for Stock."""

    OK = 10, _('OK'), ColorEnum.success  # Item is OK
    ATTENTION = 50, _('Attention needed'), ColorEnum.warning  # Item requires attention
    DAMAGED = 55, _('Damaged'), ColorEnum.warning  # Item is damaged
    DESTROYED = 60, _('Destroyed'), ColorEnum.danger  # Item is destroyed
    REJECTED = 65, _('Rejected'), ColorEnum.danger  # Item is rejected
    LOST = 70, _('Lost'), ColorEnum.dark  # Item has been lost
    QUARANTINED = (
        75,
        _('Quarantined'),
        ColorEnum.info,
    )  # Item has been quarantined and is unavailable
    RETURNED = (
        85,
        _('Returned'),
        ColorEnum.warning,
    )  # Item has been returned from a customer


class StockStatusGroups:
    """Groups for StockStatus codes."""

    # The following codes correspond to parts that are 'available' or 'in stock'
    AVAILABLE_CODES = [
        StockStatus.OK.value,
        StockStatus.ATTENTION.value,
        StockStatus.DAMAGED.value,
        StockStatus.RETURNED.value,
    ]


class StockHistoryCode(StatusCode):
    """Status codes for StockHistory."""

    LEGACY = 0, _('Legacy stock tracking entry')

    CREATED = 1, _('Stock item created')

    # Manual editing operations
    EDITED = 5, _('Edited stock item')
    ASSIGNED_SERIAL = 6, _('Assigned serial number')

    # Manual stock operations
    STOCK_COUNT = 10, _('Stock counted')
    STOCK_ADD = 11, _('Stock manually added')
    STOCK_REMOVE = 12, _('Stock manually removed')
    STOCK_SERIZALIZED = 13, _('Serialized stock items')

    RETURNED_TO_STOCK = 15, _('Returned to stock')  # Stock item returned to stock

    # Location operations
    STOCK_MOVE = 20, _('Location changed')
    STOCK_UPDATE = 25, _('Stock updated')

    # Installation operations
    INSTALLED_INTO_ASSEMBLY = 30, _('Installed into assembly')
    REMOVED_FROM_ASSEMBLY = 31, _('Removed from assembly')

    INSTALLED_CHILD_ITEM = 35, _('Installed component item')
    REMOVED_CHILD_ITEM = 36, _('Removed component item')

    # Stock splitting operations
    SPLIT_FROM_PARENT = 40, _('Split from parent item')
    SPLIT_CHILD_ITEM = 42, _('Split child item')

    # Stock merging operations
    MERGED_STOCK_ITEMS = 45, _('Merged stock items')

    # Convert stock item to variant
    CONVERTED_TO_VARIANT = 48, _('Converted to variant')

    # Build order codes
    BUILD_OUTPUT_CREATED = 50, _('Build order output created')
    BUILD_OUTPUT_COMPLETED = 55, _('Build order output completed')
    BUILD_OUTPUT_REJECTED = 56, _('Build order output rejected')
    BUILD_CONSUMED = 57, _('Consumed by build order')

    # Sales order codes
    SHIPPED_AGAINST_SALES_ORDER = 60, _('Shipped against Sales Order')

    # Purchase order codes
    RECEIVED_AGAINST_PURCHASE_ORDER = 70, _('Received against Purchase Order')

    # Return order codes
    RETURNED_AGAINST_RETURN_ORDER = 80, _('Returned against Return Order')

    # Customer actions
    SENT_TO_CUSTOMER = 100, _('Sent to customer')
    RETURNED_FROM_CUSTOMER = 105, _('Returned from customer')
