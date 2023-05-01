"""Status codes for InvenTree."""

from django.utils.translation import gettext_lazy as _


class StatusCode:
    """Base class for representing a set of StatusCodes.

    This is used to map a set of integer values to text.
    """

    colors = {}

    @classmethod
    def render(cls, key, large=False):
        """Render the value as a HTML label."""
        # If the key cannot be found, pass it back
        if key not in cls.options.keys():
            return key

        value = cls.options.get(key, key)
        color = cls.colors.get(key, 'secondary')

        span_class = f'badge rounded-pill bg-{color}'

        return "<span class='{cl}'>{value}</span>".format(
            cl=span_class,
            value=value
        )

    @classmethod
    def list(cls):
        """Return the StatusCode options as a list of mapped key / value items."""
        return list(cls.dict().values())

    @classmethod
    def text(cls, key):
        """Text for supplied status code."""
        return cls.options.get(key, None)

    @classmethod
    def items(cls):
        """All status code items."""
        return cls.options.items()

    @classmethod
    def keys(cls):
        """All status code keys."""
        return cls.options.keys()

    @classmethod
    def labels(cls):
        """All status code labels."""
        return cls.options.values()

    @classmethod
    def names(cls):
        """Return a map of all 'names' of status codes in this class

        Will return a dict object, with the attribute name indexed to the integer value.

        e.g.
        {
            'PENDING': 10,
            'IN_PROGRESS': 20,
        }
        """
        keys = cls.keys()
        status_names = {}

        for d in dir(cls):
            if d.startswith('_'):
                continue
            if d != d.upper():
                continue

            value = getattr(cls, d, None)

            if value is None:
                continue
            if callable(value):
                continue
            if type(value) != int:
                continue
            if value not in keys:
                continue

            status_names[d] = value

        return status_names

    @classmethod
    def dict(cls):
        """Return a dict representation containing all required information"""
        values = {}

        for name, value, in cls.names().items():
            entry = {
                'key': value,
                'name': name,
                'label': cls.label(value),
            }

            if hasattr(cls, 'colors'):
                if color := cls.colors.get(value, None):
                    entry['color'] = color

            values[name] = entry

        return values

    @classmethod
    def label(cls, value):
        """Return the status code label associated with the provided value."""
        return cls.options.get(value, value)

    @classmethod
    def value(cls, label):
        """Return the value associated with the provided label."""
        for k in cls.options.keys():
            if cls.options[k].lower() == label.lower():
                return k

        raise ValueError("Label not found")


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
        RETURNED: _("Returned"),
    }

    colors = {
        OK: 'success',
        ATTENTION: 'warning',
        DAMAGED: 'danger',
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
