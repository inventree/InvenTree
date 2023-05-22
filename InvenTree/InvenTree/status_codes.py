"""Status codes for InvenTree."""

from django.utils.translation import gettext_lazy as _

from generic.states import StatusCode


class PurchaseOrderStatus(StatusCode):
    """Defines a set of status codes for a PurchaseOrder."""

    # Order status codes
    PENDING = 10  # Order is pending (not yet placed)
    PLACED = 20  # Order has been placed with supplier
    COMPLETE = 30  # Order has been completed
    CANCELLED = 40  # Order was cancelled
    LOST = 50  # Order was lost
    RETURNED = 60  # Order was returned

    options = {
        PENDING: _("Pending"),
        PLACED: _("Placed"),
        COMPLETE: _("Complete"),
        CANCELLED: _("Cancelled"),
        LOST: _("Lost"),
        RETURNED: _("Returned"),
    }

    colors = {
        PENDING: 'secondary',
        PLACED: 'primary',
        COMPLETE: 'success',
        CANCELLED: 'danger',
        LOST: 'warning',
        RETURNED: 'warning',
    }

    # Open orders
    OPEN = [
        PENDING,
        PLACED,
    ]

    # Failed orders
    FAILED = [
        CANCELLED,
        LOST,
        RETURNED
    ]


class SalesOrderStatus(StatusCode):
    """Defines a set of status codes for a SalesOrder."""

    PENDING = 10  # Order is pending
    IN_PROGRESS = 15  # Order has been issued, and is in progress
    SHIPPED = 20  # Order has been shipped to customer
    CANCELLED = 40  # Order has been cancelled
    LOST = 50  # Order was lost
    RETURNED = 60  # Order was returned

    options = {
        PENDING: _("Pending"),
        IN_PROGRESS: _("In Progress"),
        SHIPPED: _("Shipped"),
        CANCELLED: _("Cancelled"),
        LOST: _("Lost"),
        RETURNED: _("Returned"),
    }

    colors = {
        PENDING: 'secondary',
        IN_PROGRESS: 'primary',
        SHIPPED: 'success',
        CANCELLED: 'danger',
        LOST: 'warning',
        RETURNED: 'warning',
    }

    # Open orders
    OPEN = [
        PENDING,
        IN_PROGRESS,
    ]

    # Completed orders
    COMPLETE = [
        SHIPPED,
    ]


class StockStatus(StatusCode):
    """Status codes for Stock."""

    OK = 10  # Item is OK
    ATTENTION = 50  # Item requires attention
    DAMAGED = 55  # Item is damaged
    DESTROYED = 60  # Item is destroyed
    REJECTED = 65  # Item is rejected
    LOST = 70  # Item has been lost
    QUARANTINED = 75  # Item has been quarantined and is unavailable
    RETURNED = 85  # Item has been returned from a customer

    options = {
        OK: _("OK"),
        ATTENTION: _("Attention needed"),
        DAMAGED: _("Damaged"),
        DESTROYED: _("Destroyed"),
        LOST: _("Lost"),
        REJECTED: _("Rejected"),
        QUARANTINED: _("Quarantined"),
    }

    colors = {
        OK: 'success',
        ATTENTION: 'warning',
        DAMAGED: 'warning',
        DESTROYED: 'danger',
        LOST: 'dark',
        REJECTED: 'danger',
        QUARANTINED: 'info'
    }

    # The following codes correspond to parts that are 'available' or 'in stock'
    AVAILABLE_CODES = [
        OK,
        ATTENTION,
        DAMAGED,
        RETURNED,
    ]


class StockHistoryCode(StatusCode):
    """Status codes for StockHistory."""

    LEGACY = 0

    CREATED = 1

    # Manual editing operations
    EDITED = 5
    ASSIGNED_SERIAL = 6

    # Manual stock operations
    STOCK_COUNT = 10
    STOCK_ADD = 11
    STOCK_REMOVE = 12

    # Location operations
    STOCK_MOVE = 20
    STOCK_UPDATE = 25

    # Installation operations
    INSTALLED_INTO_ASSEMBLY = 30
    REMOVED_FROM_ASSEMBLY = 31

    INSTALLED_CHILD_ITEM = 35
    REMOVED_CHILD_ITEM = 36

    # Stock splitting operations
    SPLIT_FROM_PARENT = 40
    SPLIT_CHILD_ITEM = 42

    # Stock merging operations
    MERGED_STOCK_ITEMS = 45

    # Convert stock item to variant
    CONVERTED_TO_VARIANT = 48

    # Build order codes
    BUILD_OUTPUT_CREATED = 50
    BUILD_OUTPUT_COMPLETED = 55
    BUILD_OUTPUT_REJECTED = 56
    BUILD_CONSUMED = 57

    # Sales order codes
    SHIPPED_AGAINST_SALES_ORDER = 60

    # Purchase order codes
    RECEIVED_AGAINST_PURCHASE_ORDER = 70

    # Return order codes
    RETURNED_AGAINST_RETURN_ORDER = 80

    # Customer actions
    SENT_TO_CUSTOMER = 100
    RETURNED_FROM_CUSTOMER = 105

    options = {
        LEGACY: _('Legacy stock tracking entry'),

        CREATED: _('Stock item created'),

        EDITED: _('Edited stock item'),
        ASSIGNED_SERIAL: _('Assigned serial number'),

        STOCK_COUNT: _('Stock counted'),
        STOCK_ADD: _('Stock manually added'),
        STOCK_REMOVE: _('Stock manually removed'),

        STOCK_MOVE: _('Location changed'),
        STOCK_UPDATE: _('Stock updated'),

        INSTALLED_INTO_ASSEMBLY: _('Installed into assembly'),
        REMOVED_FROM_ASSEMBLY: _('Removed from assembly'),

        INSTALLED_CHILD_ITEM: _('Installed component item'),
        REMOVED_CHILD_ITEM: _('Removed component item'),

        SPLIT_FROM_PARENT: _('Split from parent item'),
        SPLIT_CHILD_ITEM: _('Split child item'),

        MERGED_STOCK_ITEMS: _('Merged stock items'),

        CONVERTED_TO_VARIANT: _('Converted to variant'),

        SENT_TO_CUSTOMER: _('Sent to customer'),
        RETURNED_FROM_CUSTOMER: _('Returned from customer'),

        BUILD_OUTPUT_CREATED: _('Build order output created'),
        BUILD_OUTPUT_COMPLETED: _('Build order output completed'),
        BUILD_OUTPUT_REJECTED: _('Build order output rejected'),
        BUILD_CONSUMED: _('Consumed by build order'),

        SHIPPED_AGAINST_SALES_ORDER: _("Shipped against Sales Order"),

        RECEIVED_AGAINST_PURCHASE_ORDER: _('Received against Purchase Order'),

        RETURNED_AGAINST_RETURN_ORDER: _('Returned against Return Order'),
    }


class BuildStatus(StatusCode):
    """Build status codes."""

    PENDING = 10  # Build is pending / active
    PRODUCTION = 20  # BuildOrder is in production
    CANCELLED = 30  # Build was cancelled
    COMPLETE = 40  # Build is complete

    options = {
        PENDING: _("Pending"),
        PRODUCTION: _("Production"),
        CANCELLED: _("Cancelled"),
        COMPLETE: _("Complete"),
    }

    colors = {
        PENDING: 'secondary',
        PRODUCTION: 'primary',
        COMPLETE: 'success',
        CANCELLED: 'danger',
    }

    ACTIVE_CODES = [
        PENDING,
        PRODUCTION,
    ]


class ReturnOrderStatus(StatusCode):
    """Defines a set of status codes for a ReturnOrder"""

    # Order is pending, waiting for receipt of items
    PENDING = 10

    # Items have been received, and are being inspected
    IN_PROGRESS = 20

    COMPLETE = 30
    CANCELLED = 40

    OPEN = [
        PENDING,
        IN_PROGRESS,
    ]

    options = {
        PENDING: _("Pending"),
        IN_PROGRESS: _("In Progress"),
        COMPLETE: _("Complete"),
        CANCELLED: _("Cancelled"),
    }

    colors = {
        PENDING: 'secondary',
        IN_PROGRESS: 'primary',
        COMPLETE: 'success',
        CANCELLED: 'danger',
    }


class ReturnOrderLineStatus(StatusCode):
    """Defines a set of status codes for a ReturnOrderLineItem"""

    PENDING = 10

    # Item is to be returned to customer, no other action
    RETURN = 20

    # Item is to be repaired, and returned to customer
    REPAIR = 30

    # Item is to be replaced (new item shipped)
    REPLACE = 40

    # Item is to be refunded (cannot be repaired)
    REFUND = 50

    # Item is rejected
    REJECT = 60

    options = {
        PENDING: _('Pending'),
        RETURN: _('Return'),
        REPAIR: _('Repair'),
        REFUND: _('Refund'),
        REPLACE: _('Replace'),
        REJECT: _('Reject')
    }

    colors = {
        PENDING: 'secondary',
        RETURN: 'success',
        REPAIR: 'primary',
        REFUND: 'info',
        REPLACE: 'warning',
        REJECT: 'danger',
    }
