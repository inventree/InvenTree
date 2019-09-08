from django.utils.translation import ugettext as _


class StatusCode:

    @classmethod
    def items(cls):
        return cls.options.items()

    @classmethod
    def label(cls, value):
        """ Return the status code label associated with the provided value """
        return cls.options.get(value, value)


class OrderStatus(StatusCode):

    # Order status codes
    PENDING = 10  # Order is pending (not yet placed)
    PLACED = 20  # Order has been placed
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


class StockStatus(StatusCode):

    OK = 10  # Item is OK
    ATTENTION = 50  # Item requires attention
    DAMAGED = 55  # Item is damaged
    DESTROYED = 60  # Item is destroyed
    LOST = 70  # Item has been lost

    options = {
        OK: _("OK"),
        ATTENTION: _("Attention needed"),
        DAMAGED: _("Damaged"),
        DESTROYED: _("Destroyed"),
        LOST: _("Lost"),
    }

    # The following codes correspond to parts that are 'available'
    AVAILABLE_CODES = [
        OK,
        ATTENTION,
        DAMAGED
    ]


class BuildStatus(StatusCode):

    # Build status codes
    PENDING = 10  # Build is pending / active
    ALLOCATED = 20  # Parts have been removed from stock
    CANCELLED = 30  # Build was cancelled
    COMPLETE = 40  # Build is complete

    options = {
        PENDING: _("Pending"),
        ALLOCATED: _("Allocated"),
        CANCELLED: _("Cancelled"),
        COMPLETE: _("Complete"),
    }

    ACTIVE_CODES = [
        PENDING,
        ALLOCATED
    ]
