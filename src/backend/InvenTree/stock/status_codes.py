"""Stock status codes."""

from django.utils.translation import gettext_lazy as _

from generic.states import ColorEnum, StatusCode


class StockStatus(StatusCode):
    """Status codes for Stock.

    Attributes:
        OK: Stock item is healthy, nothing wrong to report
        ATTENTION: Stock item hasn't been checked or tested yet
        DAMAGED: Stock item is not functional in its present state
        DESTROYED: Stock item has been destroyed
        REJECTED: Stock item did not pass the quality control standards
        LOST: Stock item has been lost
        QUARANTINED: Stock item has been intentionally isolated and is unavailable
        RETURNED: Stock item has been returned from a customer
    """

    OK = 10, _('OK'), ColorEnum.success
    ATTENTION = 50, _('Attention needed'), ColorEnum.warning
    DAMAGED = 55, _('Damaged'), ColorEnum.warning
    DESTROYED = 60, _('Destroyed'), ColorEnum.danger
    REJECTED = 65, _('Rejected'), ColorEnum.danger
    LOST = 70, _('Lost'), ColorEnum.dark
    QUARANTINED = 75, _('Quarantined'), ColorEnum.info
    RETURNED = 85, _('Returned'), ColorEnum.warning


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
    """Status codes for StockHistory.

    Attributes:
        LEGACY: Legacy stock tracking entry, created before tracking entry types existed
        CREATED: Stock item created

        EDITED: Stock item was manually edited
        ASSIGNED_SERIAL: A serial number was assigned to the stock item

        STOCK_COUNT: Stock was manually counted
        STOCK_ADD: Stock was manually added
        STOCK_REMOVE: Stock was manually removed
        STOCK_SERIALIZED: Stock items were serialized

        RETURNED_TO_STOCK: Stock item was returned to stock

        STOCK_MOVE: The location of the stock item was changed
        STOCK_UPDATE: Stock item was updated

        INSTALLED_INTO_ASSEMBLY: Stock item was installed into an assembly
        REMOVED_FROM_ASSEMBLY: Stock item was removed from an assembly

        INSTALLED_CHILD_ITEM: A component item was installed into this stock item
        REMOVED_CHILD_ITEM: A component item was removed from this stock item

        SPLIT_FROM_PARENT: Stock item was split from a parent stock item
        SPLIT_CHILD_ITEM: A child stock item was split from this stock item

        MERGED_STOCK_ITEMS: Multiple stock items were merged into this one

        DISASSEMBLED: Stock item was disassembled into its component items
        CREATED_FROM_DISASSEMBLY: Stock item was created as a result of disassembly

        CONVERTED_TO_VARIANT: Stock item was converted to a variant of its part

        BUILD_OUTPUT_CREATED: Stock item was created as a build order output
        BUILD_OUTPUT_COMPLETED: Stock item (a build order output) was completed
        BUILD_OUTPUT_REJECTED: Stock item (a build order output) was rejected
        BUILD_CONSUMED: Stock item was consumed by a build order

        SHIPPED_AGAINST_SALES_ORDER: Stock item was shipped against a Sales Order

        RECEIVED_AGAINST_PURCHASE_ORDER: Stock item was received against a Purchase Order

        RETURNED_AGAINST_RETURN_ORDER: Stock item was returned against a Return Order

        SENT_TO_CUSTOMER: Stock item was sent to a customer
        RETURNED_FROM_CUSTOMER: Stock item was returned from a customer
    """

    LEGACY = 0, _('Legacy stock tracking entry')

    CREATED = 1, _('Stock item created')

    # Manual editing operations
    EDITED = 5, _('Edited stock item')
    ASSIGNED_SERIAL = 6, _('Assigned serial number')

    # Manual stock operations
    STOCK_COUNT = 10, _('Stock counted')
    STOCK_ADD = 11, _('Stock manually added')
    STOCK_REMOVE = 12, _('Stock manually removed')
    STOCK_SERIALIZED = 13, _('Serialized stock items')

    RETURNED_TO_STOCK = 15, _('Returned to stock')

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

    # Stock disassembly operations
    DISASSEMBLED = 46, _('Disassembled into components')
    CREATED_FROM_DISASSEMBLY = 47, _('Created from disassembly')

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
