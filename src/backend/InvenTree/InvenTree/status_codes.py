"""Status codes for InvenTree."""

from django.utils.translation import gettext_lazy as _

from generic.states import StatusCode


class PurchaseOrderStatus(StatusCode):
    """Defines a set of status codes for a PurchaseOrder."""

    # Order status codes
    PENDING = 10, _('Pending'), 'secondary'  # Order is pending (not yet placed)
    PLACED = 20, _('Placed'), 'primary'  # Order has been placed with supplier
    COMPLETE = 30, _('Complete'), 'success'  # Order has been completed
    CANCELLED = 40, _('Cancelled'), 'danger'  # Order was cancelled
    LOST = 50, _('Lost'), 'warning'  # Order was lost
    RETURNED = 60, _('Returned'), 'warning'  # Order was returned


class PurchaseOrderStatusGroups:
    """Groups for PurchaseOrderStatus codes."""

    # Open orders
    OPEN = [PurchaseOrderStatus.PENDING.value, PurchaseOrderStatus.PLACED.value]

    # Failed orders
    FAILED = [
        PurchaseOrderStatus.CANCELLED.value,
        PurchaseOrderStatus.LOST.value,
        PurchaseOrderStatus.RETURNED.value,
    ]


class SalesOrderStatus(StatusCode):
    """Defines a set of status codes for a SalesOrder."""

    PENDING = 10, _('Pending'), 'secondary'  # Order is pending
    IN_PROGRESS = (
        15,
        _('In Progress'),
        'primary',
    )  # Order has been issued, and is in progress
    SHIPPED = 20, _('Shipped'), 'success'  # Order has been shipped to customer
    CANCELLED = 40, _('Cancelled'), 'danger'  # Order has been cancelled
    LOST = 50, _('Lost'), 'warning'  # Order was lost
    RETURNED = 60, _('Returned'), 'warning'  # Order was returned


class SalesOrderStatusGroups:
    """Groups for SalesOrderStatus codes."""

    # Open orders
    OPEN = [SalesOrderStatus.PENDING.value, SalesOrderStatus.IN_PROGRESS.value]

    # Completed orders
    COMPLETE = [SalesOrderStatus.SHIPPED.value]


class StockStatus(StatusCode):
    """Status codes for Stock."""

    OK = 10, _('OK'), 'success'  # Item is OK
    ATTENTION = 50, _('Attention needed'), 'warning'  # Item requires attention
    DAMAGED = 55, _('Damaged'), 'warning'  # Item is damaged
    DESTROYED = 60, _('Destroyed'), 'danger'  # Item is destroyed
    REJECTED = 65, _('Rejected'), 'danger'  # Item is rejected
    LOST = 70, _('Lost'), 'dark'  # Item has been lost
    QUARANTINED = (
        75,
        _('Quarantined'),
        'info',
    )  # Item has been quarantined and is unavailable
    RETURNED = 85, _('Returned'), 'warning'  # Item has been returned from a customer


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


class BuildStatus(StatusCode):
    """Build status codes."""

    PENDING = 10, _('Pending'), 'secondary'  # Build is pending / active
    PRODUCTION = 20, _('Production'), 'primary'  # BuildOrder is in production
    CANCELLED = 30, _('Cancelled'), 'danger'  # Build was cancelled
    COMPLETE = 40, _('Complete'), 'success'  # Build is complete


class BuildStatusGroups:
    """Groups for BuildStatus codes."""

    ACTIVE_CODES = [BuildStatus.PENDING.value, BuildStatus.PRODUCTION.value]


class ReturnOrderStatus(StatusCode):
    """Defines a set of status codes for a ReturnOrder."""

    # Order is pending, waiting for receipt of items
    PENDING = 10, _('Pending'), 'secondary'

    # Items have been received, and are being inspected
    IN_PROGRESS = 20, _('In Progress'), 'primary'

    COMPLETE = 30, _('Complete'), 'success'
    CANCELLED = 40, _('Cancelled'), 'danger'


class ReturnOrderStatusGroups:
    """Groups for ReturnOrderStatus codes."""

    OPEN = [ReturnOrderStatus.PENDING.value, ReturnOrderStatus.IN_PROGRESS.value]


class ReturnOrderLineStatus(StatusCode):
    """Defines a set of status codes for a ReturnOrderLineItem."""

    PENDING = 10, _('Pending'), 'secondary'

    # Item is to be returned to customer, no other action
    RETURN = 20, _('Return'), 'success'

    # Item is to be repaired, and returned to customer
    REPAIR = 30, _('Repair'), 'primary'

    # Item is to be replaced (new item shipped)
    REPLACE = 40, _('Replace'), 'warning'

    # Item is to be refunded (cannot be repaired)
    REFUND = 50, _('Refund'), 'info'

    # Item is rejected
    REJECT = 60, _('Reject'), 'danger'
